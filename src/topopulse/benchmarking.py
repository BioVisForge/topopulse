"""Measured computational benchmarks used by the CLI and benchmark suite."""

from __future__ import annotations

import os
import platform
import time
from collections.abc import Callable
from contextlib import suppress
from typing import Any, TypeVar

import numpy as np

from . import _backend
from ._version import __version__
from .datasets import large_synthetic_network

T = TypeVar("T")


def _time(callable_: Callable[[], T]) -> tuple[T, float]:
    start = time.perf_counter()
    result = callable_()
    return result, time.perf_counter() - start


def _machine_resources() -> tuple[int | None, int | None, int | None]:
    logical = os.cpu_count()
    physical: int | None = None
    available: int | None = None
    try:
        import psutil  # type: ignore[import-untyped]

        physical = psutil.cpu_count(logical=False)
        available = int(psutil.virtual_memory().available)
    except ImportError:
        if hasattr(os, "sysconf"):
            with suppress(OSError, ValueError):
                available = int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    return logical, physical, available


def run_benchmark(nodes: int = 1000, edges: int = 10_000, frames: int = 100) -> dict[str, Any]:
    """Run real ingestion, alignment, normalization, filtering, and topology timings."""
    if nodes < 2 or edges < 1 or frames < 1:
        raise ValueError("benchmark requires nodes >= 2, edges >= 1, and frames >= 1")
    (edge_frame, activity), generation = _time(
        lambda: large_synthetic_network(nodes, edges, frames)
    )
    sources = edge_frame["source"].tolist()
    targets = edge_frame["target"].tolist()
    graph, ingestion = _time(
        lambda: _backend.IndexedGraph(sources, targets, edge_frame["type"].tolist(), True)
    )
    matrix = np.ascontiguousarray(activity.iloc[:, 1:].to_numpy(dtype=np.float64))
    _, normalization = _time(lambda: _backend.normalize_matrix(matrix, "global", None))
    _, components = _time(graph.component_labels)
    _, alignment = _time(
        lambda: _backend.alignment_index(graph.node_ids, list(activity.columns[1:]), "strict")
    )
    _, filtering = _time(lambda: _backend.top_activity_indices(matrix, min(nodes, 5000)))
    _, chunks = _time(lambda: _backend.chunk_ranges(frames, 32))
    logical, physical, available = _machine_resources()
    return {
        "nodes": nodes,
        "edges": edges,
        "frames": frames,
        "dtype": "float64",
        "raw_bytes": int(matrix.nbytes),
        "dataset_generation_seconds": generation,
        "graph_ingestion_seconds": ingestion,
        "alignment_seconds": alignment,
        "normalization_seconds": normalization,
        "filtering_seconds": filtering,
        "components_seconds": components,
        "chunk_planning_seconds": chunks,
        "topopulse": __version__,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor() or "unreported",
        "logical_cpus": logical,
        "physical_cpus": physical,
        "available_memory_bytes": available,
    }
