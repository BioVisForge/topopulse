"""Single boundary around the compiled Rust extension."""

from __future__ import annotations

import importlib
from typing import Any, cast

try:
    _rust = cast(Any, importlib.import_module("topopulse._rust"))
except ImportError as error:  # pragma: no cover - source checkout diagnostic
    raise ImportError(
        "TopoPulse's Rust extension is not installed. Run `uv run maturin develop`."
    ) from error

IndexedGraph = _rust.IndexedGraph
alignment_index = _rust.alignment_index
normalize_matrix = _rust.normalize_matrix
interpolate_matrix = _rust.interpolate_matrix
differential = _rust.differential
top_activity_indices = _rust.top_activity_indices
recommend_processing_mode = _rust.recommend_processing_mode
chunk_ranges = _rust.chunk_ranges
