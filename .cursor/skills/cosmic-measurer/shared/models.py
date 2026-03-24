"""
Shared data models for all COSMIC measurer skills.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RawMovement:
    movement_type: str  # E, R, W, X
    data_group_ref: str
    name: str
    order_hint: int
    source_line: Optional[int] = None
    execution_order: Optional[int] = None
    via_artifact: Optional[str] = None
    is_async: bool = False
