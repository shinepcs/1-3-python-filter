"""콘솔 입력과 결과 출력 형식을 담당한다."""

from typing import Any, List, Tuple

from models import Matrix, Number, PatternResult, PerformanceResult
from performance import DEFAULT_REPEAT_COUNT


def print_pattern_results(
    results: List[PatternResult],
) -> Tuple[int, int, int, List[PatternResult]]:
    """패턴별 점수와 판정 결과를 출력한다."""
    total_count: int = len(results)
    pass_count: int = 0
    failed_results: List[PatternResult] = []

    print(
        """
    #------------------
    # [2] 패턴 분석 결과
    #------------------
    """
    )

    for result in results:
        case_id: str = str(result.get("case_id", "UNKNOWN"))
        status: str = str(result.get("status", "FAIL"))
        cross_score: Any = result.get("cross_score")
        x_score: Any = result.get("x_score")
        prediction: Any = result.get("prediction")
        expected: Any = result.get("expected")
        reason: str = str(result.get("reason", ""))

        if status == "PASS":
            pass_count += 1
        else:
            failed_results.append(result)

        print(f"\n--- {case_id} ---")

        if isinstance(cross_score, (int, float)) and not isinstance(
            cross_score, bool
        ):
            print(f"Cross 점수:{cross_score:.16f}")
        else:
            print("Cross 점수: 계산 불가")

        if isinstance(x_score, (int, float)) and not isinstance(x_score, bool):
            print(f"X 점수: {x_score:.16f}")
        else:
            print("X 점수: 계산 불가")

        prediction_text: str = (
            str(prediction) if prediction is not None else "계산 불가"
        )
        expected_text: str = str(expected) if expected is not None else "확인 불가"

        print(f"판정: {prediction_text}| expected: {expected_text} {status}")

        if reason:
            print(f"사유: {reason}")

    fail_count: int = len(failed_results)

    print(
        f"""
#-------------------
# [4] 결과 요약
#-------------------
총 테스트: {total_count}개
통과: {pass_count}개
실패: {fail_count}개
"""
    )

    if failed_results:
        print("\n실패 케이스:")

        for failed_result in failed_results:
            failed_case_id: str = str(failed_result.get("case_id", "UNKNOWN"))
            failed_reason: str = str(
                failed_result.get("reason", "실패 이유가 기록되지 않았습니다")
            )
            print(f"- {failed_case_id}: {failed_reason}")
    else:
        print("\n모든 테스트가 통과 했습니다.")

    return total_count, pass_count, fail_count, failed_results


def read_matrix(title: str, size: int = 3) -> Matrix:
    """콘솔에서 size x size 숫자 행렬을 입력받는다."""
    if not isinstance(title, str):
        raise TypeError("title은 문자열이어야 합니다.")

    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("size는 양의 정수여야 합니다.")

    matrix: Matrix = []

    print(f"\n{title}: {size}줄 입력, 각 줄은 공백으로 구분")

    row_index: int = 0
    while row_index < size:
        raw_line: str = input(f"{row_index + 1}행: ").strip()
        tokens: List[str] = raw_line.split()

        if len(tokens) != size:
            print(
                f"입력 형식 오류: 각 줄에 {size}개의 숫자를 "
                "공백으로 구분해 입력하세요."
            )
            continue

        try:
            row: List[Number] = [float(token) for token in tokens]
        except ValueError:
            print("입력 형식 오류: 숫자로 변환할 수 없는 값이 있습니다.")
            continue

        matrix.append(row)
        row_index += 1

    return matrix


def print_matrix(title: str, matrix: Matrix) -> None:
    """행렬을 콘솔에 보기 좋은 형태로 출력한다."""
    print(f"\n{title}")

    for row in matrix:
        row_text: str = " ".join(f"{value:g}" for value in row)
        print(row_text)


def print_performance_report(
    results: List[PerformanceResult],
    repeat_count: int = DEFAULT_REPEAT_COUNT,
    section_number: int = 3,
) -> None:
    """크기별 MAC 성능 측정 결과를 표로 출력한다."""
    print(
        f"""\n
    #----------
    # [{section_number}] 성능 분석 (평균/{repeat_count}회)
    #----------"""
    )
    print(f"{'크기':<10}" f"{'평균 시간(ms)':>18}" f"{'연산 횟수':>14}")
    print("-" * 42)

    for size, average_ms, operation_count in results:
        size_text: str = f"{size}x{size}"
        print(
            f"{size_text:<10}"
            f"{average_ms:>18.6f}"
            f"{operation_count:>14}"
        )


def select_mode() -> str:
    """사용할 실행 모드를 선택받는다."""
    while True:
        print(
            """\n
        [모드 선택]
        1. 사용자 입력 (3x3)
        2. data.json 분석"""
        )

        choice: str = input("선택: ").strip()

        if choice in ("1", "2"):
            return choice

        print("입력 오류: 1 또는 2를 입력하세요")


def print_result_summary(
    total_count: int,
    pass_count: int,
    fail_count: int,
    failed_results: List[PatternResult],
) -> None:
    """최종 통과/실패 요약을 출력한다."""
    print(
        f"""\n
    # ----------
    # [4] 결과 요약
    # ----------
    총 테스트: {total_count}
    통과: {pass_count}
    실패: {fail_count}"""
    )

    if failed_results:
        print("\n실패 케이스:")

        for failed_result in failed_results:
            case_id: str = str(failed_result.get("case_id", "UNKNOWN"))
            reason: str = str(
                failed_result.get("reason", "실패 이유가 기록되지 않았습니다.")
            )
            print(f"- {case_id}: {reason}")
    else:
        print("\n모든 테스트가 통과했습니다.")
