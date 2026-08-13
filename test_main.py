from typing import Any, Dict, List
from main import (
    analyze_all_patterns,
    classify,
    extract_pattern_size,
    load_json,
    mac_score,
    normalize_label,
    validate_matrix
)

def test_mac_score() -> None:
    pattern = [
        [1,2],
        [3,4]
    ]

    filter_data = [
        [2,0],
        [1,2]
    ]

    result: float = mac_score(pattern, filter_data)

    assert result == 13.0
    print("mac_score 테스트 통과")

def test_normalize_label() -> None:
    assert normalize_label("+") == "Cross"
    assert normalize_label("cross") == "Cross"
    assert normalize_label("Cross") == "Cross"
    assert normalize_label(" x ") == "X"
    assert normalize_label("triangle") is None
    print("normalize_label 테스트 통과")

def test_classify() -> None:
    assert classify(5.0, 1.0) == "Cross"
    assert classify(1.0, 5.0) == "X"
    assert classify( 0.9, 0.8999999999999) == "UNDECIDED"
    print("classify 테스트 통과")

def test_validate_matrix() -> None:
    valid_matrix = [
        [1, 0],
        [0, 1]
    ]

    is_valid, error_message = validate_matrix(
        valid_matrix, 2
    )
    assert is_valid is True
    assert error_message == ""

    wrong_row_count = [
        [1, 0]
    ]

    is_valid, error_message = validate_matrix(
        wrong_row_count, 2
    )

    assert is_valid is False
    assert error_message != ""

    wrong_column_count = [
        [1, 0],
        [0]
    ]

    is_valid, error_message = validate_matrix(
        wrong_column_count, 2
    )

    assert is_valid is False
    assert error_message != ""

    non_number_matrix = [
        [1, 0],
        [0, "잘못된 값"]
    ]

    is_valid, error_message = validate_matrix(
        non_number_matrix, 2
    )

    assert is_valid is False
    assert error_message != ""

    print("validate_matrix 테스트 통과")


def test_extract_pattern_size() -> None:
    size, error_message = extract_pattern_size("size_13_2")
    assert size == 13
    assert error_message == ""

    size, error_message = extract_pattern_size("wrong_13_2")
    assert size is None
    assert error_message != ""

    size, error_message = extract_pattern_size("wrong_abc_2")
    assert size is None
    assert error_message != ""
    
    print("extract_pattern_size 테스트 통과")

def test_data_json() -> None:
    data, error_message = load_json("data.json")

    assert data is not None, error_message

    results, error_message = analyze_all_patterns(data)

    assert error_message == ""
    assert len(results) == 6

    statuses: List[str] = [
        str(result["status"])
        for result in results
    ]

    assert statuses.count("PASS") == 3
    assert statuses.count("FAIL") == 3

    predictions: Dict[str, Any] = {
        str(result["case_id"]): result["prediction"]
        for result in results
    }

    assert predictions["size_5_1"] == "UNDECIDED"
    assert predictions["size_5_2"] == "Cross"
    assert predictions["size_13_1"] == "X"
    assert predictions["size_13_2"] == "UNDECIDED"
    assert predictions["size_25_1"] == "UNDECIDED"
    assert predictions["size_25_2"] == "Cross"

    print("data.json 통합 테스트 통과")

def run_all_tests() -> None:
    test_mac_score()
    test_normalize_label()
    test_classify()
    test_validate_matrix()
    test_extract_pattern_size()
    test_data_json()

    print("\n모든 테스트가 통과했습니다.")

if __name__ == "__main__":
    run_all_tests()