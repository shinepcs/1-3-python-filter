"""MAC 연산 성능 측정과 벤치마크 데이터 구성을 담당한다."""

import time
from typing import Any, Dict, List, Optional, Tuple

from json_analysis import extract_pattern_size, get_filters_for_size
from matrix_core import (
    create_cross_matrix,
    create_x_matrix,
    mac_score,
    validate_matrix,
)
from models import BenchmarkCase, Matrix, PerformanceResult


DEFAULT_REPEAT_COUNT: int = 10


def measure_average_mac_time(
    pattern: Matrix,
    filters: List[Matrix],
    repeat_count: int = DEFAULT_REPEAT_COUNT,
) -> float:
    """여러 필터의 MAC 연산 한 번당 평균 시간을 밀리초로 측정한다."""
    if (
        isinstance(repeat_count, bool)
        or not isinstance(repeat_count, int)
        or repeat_count < 10
    ):
        raise ValueError("repeat_count는 10 이상의 정수여야 합니다.")

    if len(pattern) == 0:
        raise ValueError("패턴이 비어 있습니다.")

    size: int = len(pattern)
    is_valid, error_message = validate_matrix(pattern, size)

    if not is_valid:
        raise ValueError(f"패턴 검증 실패:{error_message}")

    if not isinstance(filters, list) or len(filters) == 0:
        raise ValueError("측정할 필터가 하나 이상 필요합니다.")

    for filter_index, filter_data in enumerate(filters):
        is_valid, error_message = validate_matrix(filter_data, size)

        if not is_valid:
            raise ValueError(
                f"{filter_index + 1} 번째 필터 검증실패:{error_message}"
            )

    # 최초 실행에 의한 영향을 줄이기 위한 준비 실행
    for filter_data in filters:
        mac_score(pattern, filter_data)

    start_ns: int = time.perf_counter_ns()

    for _ in range(repeat_count):
        for filter_data in filters:
            mac_score(pattern, filter_data)

    end_ns: int = time.perf_counter_ns()
    total_call_count: int = repeat_count * len(filters)

    return (end_ns - start_ns) / total_call_count / 1_000_000


def measure_performance(
    benchmark_cases: Dict[int, BenchmarkCase],
    repeat_count: int = DEFAULT_REPEAT_COUNT,
) -> List[PerformanceResult]:
    """크기별 벤치마크 케이스의 MAC 평균 시간을 측정한다."""
    results: List[PerformanceResult] = []

    for size in sorted(benchmark_cases.keys()):
        pattern, filters = benchmark_cases[size]
        average_ms: float = measure_average_mac_time(
            pattern,
            filters,
            repeat_count,
        )
        operation_count: int = size * size
        results.append((size, average_ms, operation_count))

    return results


def get_benchmark_pattern(
    patterns_data: Any,
    size: int,
) -> Tuple[Optional[Matrix], str]:
    """지정한 크기에서 처음 발견한 유효 패턴을 반환한다."""
    if not isinstance(patterns_data, dict):
        return None, "patterns ㄷ이터가 객체(dict)가 아닙니다."

    for pattern_key, pattern_data in patterns_data.items():
        if not isinstance(pattern_key, str) or not isinstance(pattern_data, dict):
            continue

        extracted_size, _ = extract_pattern_size(pattern_key)

        if extracted_size != size:
            continue

        matrix: Any = pattern_data.get("input")
        is_valid, _ = validate_matrix(matrix, size)

        if is_valid:
            return matrix, ""

    return None, f"{size}x{size} 성능 측정에 사용할 유효한 패턴이 없습니다."


def build_json_benchmark_cases(
    data: Any,
) -> Tuple[Dict[int, BenchmarkCase], List[str]]:
    """JSON 데이터에서 크기별 성능 측정 케이스를 구성한다."""
    cases: Dict[int, BenchmarkCase] = {}
    errors: List[str] = []

    # data.json에는 3x3 데이터가 없으므로 프로그램에서 예시 데이터를 생성한다.
    sample_cross: Matrix = create_cross_matrix(3)
    sample_x: Matrix = create_x_matrix(3)
    cases[3] = (sample_cross, [sample_cross, sample_x])

    if not isinstance(data, dict):
        errors.append("JSON 최상위 데이터가 객체(dict)가 아닙니다.")
        return cases, errors

    filters_data: Any = data.get("filters")
    patterns_data: Any = data.get("patterns")

    for size in (5, 13, 25):
        selected_filters, filter_error = get_filters_for_size(filters_data, size)

        if selected_filters is None:
            errors.append(filter_error)
            continue

        pattern, pattern_error = get_benchmark_pattern(patterns_data, size)

        if pattern is None:
            errors.append(pattern_error)
            continue

        cases[size] = (
            pattern,
            [selected_filters["Cross"], selected_filters["X"]],
        )

    return cases, errors
