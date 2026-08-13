"""행렬 검증, 생성, MAC 계산과 점수 판정을 제공한다."""

from typing import Any, Tuple

from models import Matrix

EPSILON: float = 1e-9


def mac_score(pattern: Matrix, filter_data: Matrix) -> float:
    """패턴과 필터의 같은 위치 값을 곱한 뒤 모두 더한다."""
    total: float = 0.0

    for row in range(len(pattern)):
        for col in range(len(pattern[row])):
            total += pattern[row][col] * filter_data[row][col]

    return total


def classify(
    cross_score: float,
    x_score: float,
    epsilon: float = EPSILON,
) -> str:
    """Cross와 X 점수를 비교해 표준 라벨을 반환한다."""
    if abs(cross_score - x_score) < epsilon:
        return "UNDECIDED"

    if cross_score > x_score:
        return "Cross"

    return "X"


def classify_filter_a_b(
    score_a: float,
    score_b: float,
    epsilon: float = EPSILON,
) -> str:
    """사용자 입력 모드의 A/B 필터 점수를 비교한다."""
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    if score_a > score_b:
        return "A"
    return "B"


def validate_matrix(matrix: Any, expected_size: int) -> Tuple[bool, str]:
    """행렬이 expected_size 크기의 숫자 정사각 행렬인지 검증한다."""
    if not isinstance(matrix, list):
        return False, "2차원 배열이 아닙니다."

    if len(matrix) != expected_size:
        return False, f"행 개수가 {expected_size}개가 아닙니다"

    for row_index, row in enumerate(matrix):
        if not isinstance(row, list):
            return False, f"{row_index + 1} 번째 행이 리스트가 아닙니다."

        if len(row) != expected_size:
            return (
                False,
                f"{row_index + 1}번째 행의 열 개수가 "
                f"{expected_size}개가 아닙니다.",
            )

        for col_index, value in enumerate(row):
            # bool은 int의 하위 자료형이므로 별도로 제외한다.
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return (
                    False,
                    f"{row_index + 1}행 {col_index + 1}열에"
                    f"숫자가 아닌 값({value})이 있습니다",
                )

    return True, ""


def create_cross_matrix(size: int) -> Matrix:
    """성능 측정에 사용할 Cross 기준 행렬을 생성한다."""
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("size는 양의 정수여야 합니다.")

    matrix: Matrix = [[0.0 for _ in range(size)] for _ in range(size)]
    center: int = size // 2

    for index in range(size):
        matrix[center][index] = 1.0
        matrix[index][center] = 1.0

    return matrix


def create_x_matrix(size: int) -> Matrix:
    """성능 측정에 사용할 X 기준 행렬을 생성한다."""
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError("size는 양의 정수여야 합니다.")

    matrix: Matrix = [[0.0 for _ in range(size)] for _ in range(size)]

    for index in range(size):
        matrix[index][index] = 1.0
        matrix[index][size - 1 - index] = 1.0

    return matrix
