"""프로젝트 전반에서 공유하는 타입 별칭을 정의한다."""

from typing import Any, Dict, List, Tuple, Union


Number = Union[int, float]
Matrix = List[List[Number]]
BenchmarkCase = Tuple[Matrix, List[Matrix]]
PerformanceResult = Tuple[int, float, int]
PatternResult = Dict[str, Any]
