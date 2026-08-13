"""JSON 데이터 로드, 스키마 검증, 패턴 분석을 담당한다."""

import json
from typing import Any, Dict, List, Optional, Tuple

from matrix_core import EPSILON, classify, mac_score, validate_matrix
from models import Matrix, PatternResult


def normalize_label(label: str) -> Optional[str]:
    """입력 라벨을 Cross 또는 X로 표준화한다."""
    if not isinstance(label, str):
        return None

    lowercase_label = label.strip().lower()
    if lowercase_label in ("+", "cross"):
        return "Cross"
    if lowercase_label == "x":
        return "X"
    return None


def load_json(file_path: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """JSON 객체를 파일에서 읽어 반환한다."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data: Any = json.load(file)
    except FileNotFoundError:
        return None, f"파일을 찾을 수 없습니다: {file_path}"
    except json.JSONDecodeError as error:
        return None, f"JSON 형식 오류:{error.msg}"
    except OSError as error:
        return None, f"파일 읽기 오류: {error}"

    if not isinstance(data, dict):
        return None, "JSON 최상위 데이터가 객체가 아닙니다."

    return data, ""


def extract_pattern_size(pattern_key: str) -> Tuple[Optional[int], str]:
    """size_N_idx 형식의 패턴 키에서 행렬 크기 N을 추출한다."""
    if not isinstance(pattern_key, str):
        return None, "패턴 키가 문자열이 아닙니다."

    parts: List[str] = pattern_key.split("_")

    if len(parts) != 3 or parts[0] != "size":
        return None, (
            f"잘못된 패턴 키 형식입니다: {pattern_key}\n(예: size_5_1)"
        )

    try:
        size: int = int(parts[1])
        case_index: int = int(parts[2])
    except ValueError:
        return None, f"패턴 키의 크기와 번호는 정수여야 합니다: {pattern_key}"

    if size <= 0 or case_index <= 0:
        return None, f"패턴 키의 크기와 번호는 양수여야 합니다: {pattern_key}"

    return size, ""


def get_filters_for_size(
    filters_data: Any,
    size: int,
) -> Tuple[Optional[Dict[str, Matrix]], str]:
    """지정한 크기의 Cross/X 필터를 검증하여 반환한다."""
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

        standard_label: Optional[str] = normalize_label(filter_key)

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


def analyze_pattern_case(
    pattern_key: str,
    pattern_data: Any,
    filters_data: Any,
) -> PatternResult:
    """하나의 패턴을 검증하고 Cross/X 필터로 분석한다."""
    result: PatternResult = {
        "case_id": pattern_key,
        "size": None,
        "cross_score": None,
        "x_score": None,
        "prediction": None,
        "expected": None,
        "status": "FAIL",
        "reason": "",
    }

    size, error_message = extract_pattern_size(pattern_key)

    if size is None:
        result["reason"] = error_message
        return result

    result["size"] = size

    if not isinstance(pattern_data, dict):
        result["reason"] = f"{pattern_key}: 패턴 데이터가 객체(dict)가 아닙니다"
        return result

    if "input" not in pattern_data:
        result["reason"] = f"{pattern_key}: input 값이 없습니다"
        return result

    if "expected" not in pattern_data:
        result["reason"] = f"{pattern_key}: expected 값이 없습니다."
        return result

    pattern_matrix: Any = pattern_data["input"]
    expected_raw: Any = pattern_data["expected"]

    is_valid, error_message = validate_matrix(pattern_matrix, size)

    if not is_valid:
        result["reason"] = f"{pattern_key}: 패턴 검증 실패 - {error_message}"
        return result

    if not isinstance(expected_raw, str):
        result["reason"] = f"{pattern_key}: expected 값이 문자열이 아닙니다"
        return result

    expected_label: Optional[str] = normalize_label(expected_raw)

    if expected_label is None:
        result["reason"] = (
            f"{pattern_key}: 알 수 없는 expected 라벨입니다: {expected_raw}"
        )
        return result

    result["expected"] = expected_label

    selected_filters, error_message = get_filters_for_size(filters_data, size)

    if selected_filters is None:
        result["reason"] = f"{pattern_key}: 필터 검증 실패 - {error_message}"
        return result

    cross_filter: Matrix = selected_filters["Cross"]
    x_filter: Matrix = selected_filters["X"]
    cross_score: float = mac_score(pattern_matrix, cross_filter)
    x_score: float = mac_score(pattern_matrix, x_filter)

    result["cross_score"] = cross_score
    result["x_score"] = x_score

    prediction: str = classify(cross_score, x_score)
    result["prediction"] = prediction

    if prediction == expected_label:
        result["status"] = "PASS"
        result["reason"] = ""
    elif prediction == "UNDECIDED":
        result["reason"] = (
            f"두 점수의 차이가 {EPSILON} 미만이므로 UNDECIDED로 판정되었습니다."
        )
    else:
        result["reason"] = (
            f"판정 결과({prediction})가 expected({expected_label})와 다릅니다"
        )

    return result


def analyze_all_patterns(data: Any) -> Tuple[List[PatternResult], str]:
    """JSON 데이터의 모든 패턴을 분석하여 결과 리스트를 반환한다."""
    results: List[PatternResult] = []

    if not isinstance(data, dict):
        return results, "JSON. 최상위 데이터가 객체(dict)가 아닙니다."

    filters_data: Any = data.get("filters")
    patterns_data: Any = data.get("patterns")

    if not isinstance(filters_data, dict):
        return results, "filters 값이 없거나 객체(dict)가 아닙니다."

    if not isinstance(patterns_data, dict):
        return results, "patterns 값이 없거나 객체(dict)가 아닙니다."

    for pattern_key, pattern_data in patterns_data.items():
        if not isinstance(pattern_key, str):
            invalid_result: PatternResult = {
                "case_id": str(pattern_key),
                "size": None,
                "cross_score": None,
                "x_score": None,
                "prediction": None,
                "expected": None,
                "status": "FAIL",
                "reason": "패턴 키가 문자열이 아닙니다",
            }
            results.append(invalid_result)
            continue

        result: PatternResult = analyze_pattern_case(
            pattern_key,
            pattern_data,
            filters_data,
        )
        results.append(result)

    if len(results) == 0:
        return results, "분석할 패턴이 없습니다."

    return results, ""


def get_analysis_summary(
    results: List[PatternResult],
) -> Tuple[int, int, int, List[PatternResult]]:
    """전체 분석 결과에서 통과와 실패 건수를 집계한다."""
    total_count: int = len(results)
    failed_results: List[PatternResult] = [
        result for result in results if result.get("status") != "PASS"
    ]
    fail_count: int = len(failed_results)
    pass_count: int = total_count - fail_count

    return total_count, pass_count, fail_count, failed_results
