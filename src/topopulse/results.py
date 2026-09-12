"""Structured operation results."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AnimationResult:
    output_path: Path
    frame_count: int
    render_dimensions: tuple[int, int]
    time_range: tuple[str, str]
    node_count: int
    edge_count: int
    filtered_nodes: int = 0
    filtered_edges: int = 0
    normalization: dict[str, str] = field(default_factory=dict)
    metadata_path: Path | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["output_path"] = str(self.output_path)
        result["metadata_path"] = str(self.metadata_path) if self.metadata_path else None
        return result
