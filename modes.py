"""사용자 입력 모드와 JSON 분석 모드의 실행 흐름을 담당한다."""

from typing import Any, Dict, List

from console_ui import (
    print_matrix,
    print_pattern_results,
    print_performance_report,
    print_result_summary,
    read_matrix,
)
from json_analysis import (
    analyze_all_patterns,
    get_analysis_summary,
    get_filters_for_size,
    load_json,
)
from matrix_core import EPSILON, classify_filter_a_b, mac_score
from models import BenchmarkCase, Matrix, PerformanceResult
from performance import (
    DEFAULT_REPEAT_COUNT,
    build_json_benchmark_cases,
    measure_performance,
)


def run_user_input_mode(repeat_count: int = DEFAULT_REPEAT_COUNT) -> None:
    """사용자가 입력한 3x3 필터 두 개와 패턴을 분석한다."""
    print(
        """\n
    #----------
    # [1] 필터 입력
    # ----------"""
    )

    filter_a: Matrix = read_matrix("필터 A", 3)
    filter_b: Matrix = read_matrix("필터 B", 3)

    print("\n저장된 필터를 확인합니다")
    print_matrix("필터 A", filter_a)
    print_matrix("필터 B", filter_b)

    print(
        """\n
    #----------
    # [2] 패턴 입력
    # #----------"""
    )

    pattern: Matrix = read_matrix("패턴", 3)
    score_a: float = mac_score(pattern, filter_a)
    score_b: float = mac_score(pattern, filter_b)
    decision: str = classify_filter_a_b(score_a, score_b)

    print(
        f"""\n
    #----------
    # [3] MAC 결과
    # ----------
    # A 점수: {score_a:.16f}
    # B 점수: {score_b:.16f}"""
    )

    if decision == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {decision}")

    benchmark_cases: Dict[int, BenchmarkCase] = {
        3: (pattern, [filter_a, filter_b])
    }
    performance_results: List[PerformanceResult] = measure_performance(
        benchmark_cases,
        repeat_count,
    )
    print_performance_report(performance_results, repeat_count, 4)


def run_json_mode(
    file_path: str = "data.json",
    repeat_count: int = DEFAULT_REPEAT_COUNT,
) -> None:
    """JSON 파일의 모든 패턴을 분석하고 성능 결과를 출력한다."""
    data, error_message = load_json(file_path)

    if data is None:
        print(f"오류: {error_message}")
        return

    print(
        """
#-------------------
# [1] 필터 로드
#-------------------"""
    )

    filters_data: Any = data.get("filters")

    for size in (5, 13, 25):
        selected_filters, filter_error = get_filters_for_size(filters_data, size)

        if selected_filters is None:
            print(f"✗ size_{size}: {filter_error}")
        else:
            print(f"✓ size_{size} 필터 로드 완료 (Cross, X)")

    results, error_message = analyze_all_patterns(data)

    if error_message:
        print(f"분석 오류: {error_message}")
        return

    print_pattern_results(results)

    benchmark_cases, benchmark_errors = build_json_benchmark_cases(data)
    performance_results = measure_performance(benchmark_cases, repeat_count)
    print_performance_report(performance_results, repeat_count, 3)

    if benchmark_errors:
        print("\n성능 측정 제외 사유:")

        for error in benchmark_errors:
            print(f"- {error}")

    summary = get_analysis_summary(results)
    print_result_summary(*summary)
