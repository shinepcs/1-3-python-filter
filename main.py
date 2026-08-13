"""Mini NPU Simulator의 공개 API와 실행 진입점."""

from pathlib import Path

# 기존에 main에서 제공하던 이름을 다시 노출해 이전 import 방식을 유지한다.
from console_ui import (
    print_matrix,
    print_pattern_results,
    print_performance_report,
    print_result_summary,
    read_matrix,
    select_mode,
)
from json_analysis import (
    analyze_all_patterns,
    analyze_pattern_case,
    extract_pattern_size,
    get_analysis_summary,
    get_filters_for_size,
    load_json,
    normalize_label,
)
from matrix_core import (
    EPSILON,
    classify,
    classify_filter_a_b,
    create_cross_matrix,
    create_x_matrix,
    mac_score,
    validate_matrix,
)
from models import BenchmarkCase, Matrix, Number, PatternResult, PerformanceResult
from modes import run_json_mode, run_user_input_mode
from performance import (
    DEFAULT_REPEAT_COUNT,
    build_json_benchmark_cases,
    get_benchmark_pattern,
    measure_average_mac_time,
    measure_performance,
)


__all__ = [
    "BenchmarkCase",
    "DEFAULT_REPEAT_COUNT",
    "EPSILON",
    "Matrix",
    "Number",
    "PatternResult",
    "PerformanceResult",
    "analyze_all_patterns",
    "analyze_pattern_case",
    "build_json_benchmark_cases",
    "classify",
    "classify_filter_a_b",
    "create_cross_matrix",
    "create_x_matrix",
    "extract_pattern_size",
    "get_analysis_summary",
    "get_benchmark_pattern",
    "get_filters_for_size",
    "load_json",
    "mac_score",
    "main",
    "measure_average_mac_time",
    "measure_performance",
    "normalize_label",
    "print_matrix",
    "print_pattern_results",
    "print_performance_report",
    "print_result_summary",
    "read_matrix",
    "run_json_mode",
    "run_user_input_mode",
    "select_mode",
    "validate_matrix",
]


def main() -> None:
    """실행 모드를 선택하고 Mini NPU Simulator를 시작한다."""
    print("=== Mini NPU Simulator ===")

    mode: str = select_mode()

    if mode == "1":
        run_user_input_mode()
    else:
        json_file_path = Path(__file__).resolve().with_name("data.json")
        run_json_mode(str(json_file_path))


if __name__ == "__main__":
    main()
