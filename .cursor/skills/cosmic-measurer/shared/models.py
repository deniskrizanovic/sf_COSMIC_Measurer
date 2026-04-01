"""
Shared data models for all COSMIC measurer skills.
"""

from dataclasses import dataclass
from typing import Literal, Optional

MovementType = Literal["E", "R", "W", "X"]


@dataclass
class RawMovement:
    movement_type: MovementType
    data_group_ref: str
    name: str
    order_hint: int
    source_line: Optional[int] = None
    execution_order: Optional[int] = None
    via_artifact: Optional[str] = None
    is_async: bool = False


@dataclass
class LwcRawMovement(RawMovement):
    tier: Optional[int] = None
    tier_label: Optional[str] = None
    block_label: Optional[str] = None
    triggering_block: Optional[str] = None
    handler_names: Optional[list[str]] = None
