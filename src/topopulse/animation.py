"""Streaming animation encoding."""

from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import imageio.v2 as imageio
import matplotlib.pyplot as plt
import numpy as np

from .config import EdgeStyle, NetworkConfig, NodeStyle
from .errors import RenderingError
from .graph import GraphData
from .io import EdgeTemporalData, ensure_matching_times
from .layouts import Positions
from .rendering import figure_rgb, frame_attributes, render_frame
from .results import AnimationResult
from .temporal import TemporalData


@dataclass(frozen=True)
class Event:
    time: Any
    label: str


def _normalization_params(style: NodeStyle | EdgeStyle) -> tuple[float, float] | None:
    if style.normalization == "fixed":
        return style.fixed_range
    if style.normalization == "percentile":
        return style.percentile_range
    return None


def _frame_repetitions(times: tuple[Any, ...], config: NetworkConfig) -> list[int]:
    if config.animation.time_mode == "uniform" or len(times) < 2:
        return [1] * len(times)
    if config.animation.time_mode == "custom":
        durations = config.animation.custom_durations
        if durations is None or len(durations) != len(times):
            raise ValueError("custom time mode requires one custom duration per frame")
        return [max(1, round(duration * config.animation.fps)) for duration in durations]
    try:
        numeric = (
            np.asarray(times, dtype="datetime64[ns]").astype(np.int64)
            if any(isinstance(time, (datetime, np.datetime64)) for time in times)
            else np.asarray(times, dtype=float)
        )
    except (TypeError, ValueError) as error:
        raise ValueError(
            "proportional timing requires numeric or datetime-like time values"
        ) from error
    gaps = np.diff(numeric.astype(float))
    if np.any(gaps <= 0):
        raise ValueError("proportional timing requires strictly increasing times")
    scaled = gaps / gaps.min()
    return [max(1, round(value)) for value in scaled] + [1]


def _frames(
    graph: GraphData,
    node_data: TemporalData,
    edge_data: EdgeTemporalData | None,
    positions: Positions,
    config: NetworkConfig,
    events: list[Event],
) -> Iterator[np.ndarray]:
    node_normalized = node_data.normalized(
        config.node_style.normalization, _normalization_params(config.node_style)
    )
    edge_normalized = (
        edge_data.normalized(
            config.edge_style.normalization, _normalization_params(config.edge_style)
        )
        if edge_data is not None
        else None
    )
    repetitions = _frame_repetitions(node_data.times, config)
    for frame_index, time in enumerate(node_data.times):
        attrs = frame_attributes(
            graph,
            node_normalized[frame_index],
            edge_normalized[frame_index] if edge_normalized is not None else None,
            node_data.values[frame_index],
            edge_data.values[frame_index] if edge_data is not None else None,
            config.node_style,
            config.edge_style,
        )
        current_events = [event.label for event in events if str(event.time) == str(time)]
        fig, _ = render_frame(
            graph,
            positions,
            attrs,
            title=f"Time: {node_data.display_labels[frame_index]}",
            event_labels=current_events,
            resolution=config.animation.resolution,
            dpi=config.animation.dpi,
        )
        image = figure_rgb(fig)
        plt.close(fig)
        for _ in range(repetitions[frame_index]):
            yield image


def _network_hash(graph: GraphData) -> str:
    canonical = graph.edges.to_csv(index=False).encode()
    return hashlib.sha256(canonical).hexdigest()


def animate(
    graph: GraphData,
    node_data: TemporalData,
    edge_data: EdgeTemporalData | None,
    positions: Positions,
    output: str | Path,
    config: NetworkConfig,
    events: list[Event] | None = None,
    *,
    filtered_nodes: int = 0,
    filtered_edges: int = 0,
) -> AnimationResult:
    ensure_matching_times(node_data, edge_data)
    path = Path(output)
    suffix = path.suffix.lower()
    if suffix not in {".gif", ".mp4", ".webm"}:
        raise ValueError("animation output must be GIF, MP4, or WebM")
    if suffix in {".mp4", ".webm"} and shutil.which("ffmpeg") is None:
        raise RenderingError("FFmpeg is required for MP4/WebM output; install ffmpeg and retry")
    _frame_repetitions(node_data.times, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    writer_options: dict[str, Any] = {"fps": config.animation.fps}
    if suffix == ".gif":
        writer_options = {"duration": 1000.0 / config.animation.fps, "loop": config.animation.loop}
    else:
        writer_options["codec"] = config.animation.codec if suffix == ".mp4" else "libvpx-vp9"
        writer_options["macro_block_size"] = 2
        if config.animation.bitrate:
            writer_options["bitrate"] = config.animation.bitrate
    count = 0
    try:
        with cast(Any, imageio.get_writer(path, **writer_options)) as writer:
            for frame in _frames(graph, node_data, edge_data, positions, config, events or []):
                writer.append_data(frame)
                count += 1
    except Exception as error:
        raise RenderingError(f"failed to encode {suffix[1:].upper()} output: {error}") from error
    metadata_path = path.with_suffix(".metadata.json") if config.animation.emit_metadata else None
    if metadata_path:
        metadata = {
            "package": "topopulse",
            "version": "0.1.0",
            "network_sha256": _network_hash(graph),
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "time_points": [str(value) for value in node_data.times],
            "layout": config.layout.name,
            "layout_seed": config.layout.seed,
            "normalization": {
                "nodes": config.node_style.normalization,
                "edges": config.edge_style.normalization,
            },
            "filtering": config.filtering.model_dump(),
            "visual_mappings": {
                "nodes": config.node_style.model_dump(),
                "edges": config.edge_style.model_dump(),
            },
            "fps": config.animation.fps,
            "resolution": config.animation.resolution,
            "codec": config.animation.codec,
            "created_utc": datetime.now(UTC).isoformat(),
        }
        metadata_path.write_text(
            json.dumps(metadata, indent=2, default=str) + "\n", encoding="utf-8"
        )
    return AnimationResult(
        path,
        count,
        config.animation.resolution,
        (str(node_data.times[0]), str(node_data.times[-1])),
        graph.node_count,
        graph.edge_count,
        filtered_nodes=filtered_nodes,
        filtered_edges=filtered_edges,
        normalization={
            "nodes": config.node_style.normalization,
            "edges": config.edge_style.normalization,
        },
        metadata_path=metadata_path,
    )
