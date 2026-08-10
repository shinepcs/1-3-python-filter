import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import time

# 하나의 숫자는 정수 또는 실수일 수 있다.
# 타입 별칭. Union[int, float]을 Number로 정의 한다.
Number = Union[int, float]

# 행렬은 숫자 리스트를 여러 개 담은 2차원 리스트이다.
# 타입 별칭 List[List[Number]] 를 Matrix로 부르겠다. 변수 할당과 문법 같음.
Matrix = List[List[Number]]

EPSILON:float = 1e-9

def mac_score(pattern: Matrix, filter_data: Matrix) -> float:
    # 패턴과 필터의 같은 위치 값을 곱한 후 모두 더한다.
    total: float = 0.0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_data[row][col]

    return total

# 라벨을 Cross 또는 X 로 표준화 한다.
def normalize_lable(label: str) -> Optional[str]:
    if not isinstance(label, str): return None    
    lowcaseLabel = str(label).strip().lower()
    if lowcaseLabel in ("+", "cross"): return "Cross"
    if lowcaseLabel == "x": return "X"
    return None

def classify(cross_score: float,
             x_score: float,
             epsilon: float = EPSILON) -> str:
    
    if abs(cross_score - x_score) < epsilon:
        return "UNDECIDED"

    if cross_score > x_score:
        return "Cross"

    return "X"

def validate_matrix(matrix: Any, expected_size: int
                    ) -> Tuple[bool, str]:
    if not isinstance(matrix, list):
        return (
            False, "2차원 배열이 아닙니다."
            )

    if len(matrix) != expected_size:
        return (
            False, 
            f"행 개수가 {expected_size}개가 아닙니다"
        )

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            return (False, f"{row_index + 1} 번째 행이 리스트가 아닙니다.")

        if len(row) != expected_size:
            return (False,
                f"{row_index + 1}번째 행의 열 개수가 "
                f"{expected_size}개가 아닙니다."
            )

        for col_index, value in enumerate(row):
            # bool은 int의 하위 자료형이므로 별도로 제외한다.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return (False, 
                        f"{row_index+1}행 {col_index+1}열에"
                        f"숫자가 아닌 값({value})이 있습니다")

    return True, ""

def load_json(file_path: str) -> Tuple[Optional[Dict[str, Any]], str]:

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data: Any = json.load(file)

    except FileNotFoundError: return None, f"파일을 찾을 수 없습니다: {file_path}"
    except json.JSONDecodeError as error: return None, f"JSON 형식 오류:{error.msg}"
    except OSError as error: return None, f"파일 읽기 오류: {error}"

    if not isinstance(data, dict):
        return None, "JSON 최상위 데이터가 객체가 아닙니다."

    return data, ""

def extract_pattern_size(pattern_key:str) -> Tuple[Optional[int], str]:
    # size_N_idx 형식의 패턴 키에서 행렬 크기 N을 추출한다.
    if not isinstance(pattern_key, str):
        return None, "패턴 키가 문자열이 아닙니다."

    parts: List[str] = pattern_key.split("_")

    if len(parts) != 3 or parts[0] != "size":
        return None, (
            f"잘못된 패턴 키 형식입니다: {pattern_key}\n(예: size_5_1)")

    try:
        size: int = int(parts[1])
        case_index: int = int(parts[2])
    except ValueError:
        return None, f"패턴 키의 크기와 번호는 정수여야 합니다: {pattern_key}"

    if size <= 0 or case_index <= 0:
        return None, f"패턴 키의 크기와 번호는 양수여야 합니다: {pattern_key}"

    return size, ""


def get_filters_for_size( filters_data: Any, size:int
    )-> Tuple[Optional[dict[str, Matrix]], str]:

    #지정한 크기의 Cross/X 필터를 검증하여 반환한다.
    if not isinstance(filters_data, dict):
        return None, "filters 데이터가 객체(dict)가 아닙니다."

    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        return None, "필터 크기는 양의 정수여야 합니다."
    size_key: str = f"size_{size}"
    filter_group: Any = filters_data.get(size_key)

    if not isinstance(filter_group, dict):
        return None, f"{size_key} 필터가 없거나 객체(dict)가 아닙니다."

    normalized_filters: Dict[str, Matrix] = {}

    for filter_key, matrix in filter_group.items():
        if not isinstance(filter_key, str):
            return None, f"{size_key}에 문자열이 아닌 필터 키가 있습니다."

        standard_label: Optional[str] = normalize_lable(filter_key)

        if standard_label is None:
            return None, f"알 수 없는 필터 라벨입니다: {filter_key}"

        is_valid, error_message = validate_matrix(matrix, size)

        if not is_valid:
            return None, f"{size_key}/{filter_key}: {error_message}"

        normalized_filters[standard_label] = matrix

    for required_label in ("Cross", "X"):
        if required_label not in normalized_filters:
            return None, f"{size_key}에 {required_label} 필터가 없습니다."

    return normalized_filters, ""

# 패턴 한 개의 분석 결과를 저장
PatternResult = Dict[str, Any]

def analyze_pattern_case(
        pattern_key: str, 
        pattern_data: Any,
        filters_data: Any
        ) -> PatternResult:

    result: PatternResult = {
        "case_id": pattern_key,
        "size": None,
        "cross_score": None,
        "x_score": None,
        "prediction": None,
        "expected": None,
        "status": "FAIL",
        "reason": ""
    }

    # 1. 패턴 키에서 크기 추출
    size, error_message = extract_pattern_size(pattern_key)

    if size is None:
        result["reason"] = error_message
        return result

    result["size"] = size

    # 2. 패턴 데이터가 dict인지 검사
    if not isinstance(pattern_data, dict):
        result["reason"] = f"{pattern_key}: 패턴 데이터가 객체(dict)가 아닙니다"
        return result

    # 3. input 키 존재 여부 검사
    if "input" not in pattern_data:
        result["reason"] = f"{pattern_key}: input 값이 없습니다"
        return result

    # 4. expected 키 존재 여부 검사
    if "expected" not in pattern_data:
        result["reason"] = f"{pattern_key}: expected 값이 없습니다."
        return result

    pattern_matrix: Any = pattern_data["input"]
    expected_raw: Any = pattern_data["expected"]

    # 5. 패턴 행렬 크기와 숫자 여부 검사
    is_valid, error_message = validate_matrix(pattern_matrix, size)

    if not is_valid:
        result["reason"] = f"{pattern_key}: 패턴 검증 실패 - {error_message}"
        return result

    # 6. expected가 문자열인지 검사
    if not isinstance(expected_raw, str):
        result["reason"] = f"{pattern_key}: expected 값이 문자열이 아닙니다"
        return result

    # 7. expected 라벨 정규화
    expected_label: Optional[str] = normalize_lable(expected_raw)

    if expected_label is None:
        result["reason"] = f"{pattern_key}: 알 수 없는 expected 라벨입니다: {expected_raw}"
        return result

    result["expected"] = expected_label

    # 8. 패턴 크기에 맞는 Crosss/X 필터 가져오기
    selected_filters, error_message = get_filters_for_size(filters_data, size)

    if selected_filters is None:
        result["reason"] = f"{pattern_key}: 필터 검증 실패 - {error_message}"
        return result

    cross_filter: Matrix = selected_filters["Cross"]
    x_filter: Matrix = selected_filters["X"]

    # 9. Cross 필터와 X 필터의 MAC 점수 계산
    cross_score:float = mac_score(pattern_matrix, cross_filter)
    x_score:float = mac_score(pattern_matrix, x_filter)
    result["cross_score"] = cross_score
    result["x_score"] = x_score

    # 10. epsilon 정책을 적용하여 최종 판정
    prediction: str = classify(cross_score, x_score)

    result["prediction"] = prediction

    # 11. 판정 결과와 expected 비교
    if prediction == expected_label:
        result["status"] = "PASS"
        result["reason"] = ""
    else:
        result["status"] = "FAIL"

        if prediction == "UNDECIDED":
            result["reason"] = f"두 점수의 차이가 {EPSILON} 미만이므로 UNDECIDED로 판정되었습니다."
        else:
            result["reason"] = f"판정 결과({prediction}가 expected({expected_label})와 다릅니다"
    return result


def analyze_all_patterns(data: Any) -> Tuple[List[PatternResult], str]:
    # JSON 데이터의 모든 패턴을 분석하여 결과 리스트를 반환한다.

    results: List[PatternResult] = []

    # 1. 최상의 데이터 검사
    if not isinstance(data, dict):
        return results, "JSON. 최상위 데이터가 객체(dict)가 아닙니다."

    # 2. filters오ㅘ patterns 가져오기
    filters_data: Any = data.get("filters")
    patterns_data: Any = data.get("patterns")

    # 3. filters 구조 검사
    if not isinstance(filters_data, dict):
        return results, f"filters 값이 없거나 객체(dict)가 아닙니다."

    # 4. patterns 구조 검사
    if not isinstance(patterns_data, dict):
        return results, f"patterns 값이 없거나 객체(dict)가 아닙니다."

    # 5. 모든 패턴을 하나씩 분석
    for pattern_key, pattern_data in patterns_data.items():
        if not isinstance(pattern_key, str):
            invalid_result: PatternResult = {
                "case_id":str(pattern_key),
                "size": None,
                "cross_score": None,
                "x_scorer": None,
                "prediction": None,
                "expected":None,
                "status": "FAIL",
                "reason": "패턴 키가 문자열이 아닙니다"
            }

            results.append(invalid_result)
            continue
        result: PatternResult = analyze_pattern_case(
            pattern_key, pattern_data, filters_data)

        results.append(result)
    # 6. 패턴이 하나도 없는 경우
    if len(results) == 0:
        return results, "분석할 패턴이 없습니다."

    return results, ""


def print_analysis_report(results:List[PatternResult]
) -> Tuple[int, int, int, List[PatternResult]]:

    total_count:int = len(results)
    pass_count:int = 0
    failed_results: List[PatternResult] = []

    print(
    """
    #------------------
    # [2] 패턴 분석 결과
    #------------------
    """)

    for result in results:
        case_id: str = str(result.get("case_id", "UNKNOWN"))

        status: str = str(result.get("status", "FAIL"))

        cross_score: Any = result.get("cross_score")
        x_score: Any = result.get("x_score")
        prediction: Any = result.get("prediction")
        expected:Any = result.get("expected")
        reason: str = str(result.get("reason", ""))

        if status == "PASS":
            pass_count += 1
        else:
            failed_results.append(result)

        print(f"\n--- {case_id} ---")

        if isinstance(cross_score, (int, float)) and not isinstance(cross_score, bool):
            print(f"Cross 점수:{cross_score:.16f}")
        else:
            print("Cross 점수: 계산 불가")

        if isinstance(x_score, (int, float)) and not isinstance(x_score, bool):
            print(f"X 점수: {x_score:.16}")
        else:
            print("X 점수: 계산 불가")

        prediction_text: str = (str(prediction) if prediction is not None else "계산 불가")
        expected_text: str = (str(expected) if expected is not None else "확인 불가")

        print(f"판정: {prediction_text}| expected: {expected_text} {status}")

        if reason:
            print(f"사유: {reason}")

    fail_count: int = len(failed_results)

    print(f"""
#-------------------
# [4] 결과 요약
#-------------------
총 테스트: {total_count}개
통과: {pass_count}개
실패: {fail_count}개
""")

    if failed_results:
        print("\n실패 케이스:")

        for failed_result in failed_results:
            failed_case_id: str = str(failed_result.get("case_id", "UNKNOWN"))
            failed_reason: str = str(failed_result.get("reason", "실패 이유가 기록되지 않았습니다"))
            print(f"- {failed_case_id}: {failed_reason}")
    else:
        print("\n모든 테스트가 통과 했습니다.")

    return (total_count, pass_count, fail_count, failed_results)


def test():
    project_dir = Path(__file__).resolve().parent
    json_file_path: str = str(project_dir / "data.json")

    # 1. JSON 파일 읽기
    data, error_message = load_json(json_file_path)

    if data is None:
        print(f"오류: {error_message}")
        return

    # 2. 패턴 분석
    results, error_message = analyze_all_patterns(data)

    if error_message:
        print(f"분석 오류: {error_message}")
        return

    # 3. 분석 결과 출력
    total_count, pass_count, fail_count, failed_results = print_analysis_report(results)

    print(f"total_count:{total_count}, pass_count:{pass_count}, fail_count:{fail_count}, failed_results:{failed_results}")


# 진입점: 분석할 JSON 파일 경로
if __name__ == "__main__":
    test()