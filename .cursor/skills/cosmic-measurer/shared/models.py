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
    tier: Optional[int] = None              # 1=Init, 2=Interactions, 3=Terminal
    tier_label: Optional[str] = None        # "Init", "Interactions", "Terminal"
    block_label: Optional[str] = None       # for E movements: block classification key
    triggering_block: Optional[str] = None  # for R/X in Interactions: which block triggered this
    handler_names: Optional[list] = None    # for E block movements: JS handler method names found in block
