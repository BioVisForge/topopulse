"""Publication-quality Matplotlib rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.patches import FancyArrowPatch

from .config import EdgeStyle, NodeStyle
from .graph import GraphData
from .layouts import Positions


@dataclass(frozen=True)
class FrameAttributes:
    node_colors: np.ndarray
    node_sizes: np.ndarray
    node_alpha: np.ndarray
    edge_colors: np.ndarray
    edge_widths: np.ndarray
    edge_alpha: np.ndarray
    edge_reverse: np.ndarray
    node_missing: np.ndarray
    edge_missing: np.ndarray


def _rescale(values: np.ndarray, output_range: tuple[float, float]) -> np.ndarray:
    low, high = output_range
    return low + np.clip(values, 0.0, 1.0) * (high - low)


def frame_attributes(
    graph: GraphData,
    node_normalized: np.ndarray | None,
    edge_normalized: np.ndarray | None,
    node_raw: np.ndarray | None,
    edge_raw: np.ndarray | None,
    node_style: NodeStyle,
    edge_style: EdgeStyle,
) -> FrameAttributes:
    node_missing = (
        np.ones(graph.node_count, dtype=bool) if node_raw is None else ~np.isfinite(node_raw)
    )
    edge_missing = (
        np.ones(graph.edge_count, dtype=bool) if edge_raw is None else ~np.isfinite(edge_raw)
    )
    node_scaled = (
        np.full(graph.node_count, 0.5)
        if node_normalized is None
        else np.nan_to_num(node_normalized, nan=0.5)
    )
    edge_scaled = (
        np.full(graph.edge_count, 0.5)
        if edge_normalized is None
        else np.nan_to_num(edge_normalized, nan=0.5)
    )
    node_colors = colormaps[node_style.cmap](np.clip(node_scaled, 0.0, 1.0))
    node_sizes = (
        _rescale(node_scaled, node_style.size_range)
        if node_style.size_by
        else np.full(graph.node_count, np.mean(node_style.size_range))
    )
    node_alpha = node_scaled if node_style.opacity_by else np.ones(graph.node_count)
    if edge_style.color_by:
        edge_colors = colormaps[edge_style.cmap](np.clip(edge_scaled, 0.0, 1.0))
    else:
        semantic_colors = {
            "activation": edge_style.activation_color,
            "inhibition": edge_style.inhibition_color,
        }
        edge_colors = np.asarray(
            [
                mcolors.to_rgba(semantic_colors.get(str(kind), edge_style.color))
                for kind in graph.edges["type"]
            ]
        )
    width_values = (
        2.0 * np.abs(edge_scaled - 0.5) if edge_style.normalization == "symmetric" else edge_scaled
    )
    edge_widths = (
        _rescale(width_values, edge_style.width_range)
        if edge_style.width_by
        else np.full(graph.edge_count, np.mean(edge_style.width_range))
    )
    edge_alpha = edge_scaled if edge_style.opacity_by else np.ones(graph.edge_count)
    reverse = np.zeros(graph.edge_count, dtype=bool)
    if edge_style.direction == "flux" and edge_raw is not None:
        reverse = np.asarray(edge_raw) < 0
    if node_style.missing_policy == "transparent":
        node_alpha[node_missing] = 0.0
    elif node_style.missing_policy in {"neutral", "color"}:
        node_colors[node_missing] = mcolors.to_rgba(node_style.missing_color)
    elif node_style.missing_policy == "hide":
        node_alpha[node_missing] = 0.0
    if edge_style.missing_policy == "transparent" or edge_style.missing_policy == "hide":
        edge_alpha[edge_missing] = 0.0
    return FrameAttributes(
        node_colors,
        node_sizes,
        node_alpha,
        edge_colors,
        edge_widths,
        edge_alpha,
        reverse,
        node_missing,
        edge_missing,
    )


def _draw_edge(
    ax: Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    edge_type: str,
    color: Any,
    width: float,
    alpha: float,
    reverse: bool,
) -> None:
    if reverse:
        start, end = end, start
    arrowstyle = "-"
    if edge_type in {"activation", "reaction", "transport", "unknown"}:
        arrowstyle = "-|>"
    elif edge_type == "inhibition":
        arrowstyle = "-["
    elif edge_type in {"undirected", "association"}:
        arrowstyle = "-"
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=arrowstyle,
        mutation_scale=15,
        linewidth=float(width),
        color=color,
        alpha=float(alpha),
        shrinkA=15,
        shrinkB=15,
        connectionstyle="arc3,rad=0.03",
    )
    ax.add_patch(patch)


def render_frame(
    graph: GraphData,
    positions: Positions,
    attributes: FrameAttributes,
    *,
    title: str | None = None,
    event_labels: list[str] | None = None,
    resolution: tuple[int, int] = (1280, 720),
    dpi: int = 120,
    show_labels: bool | None = None,
) -> tuple[Figure, Axes]:
    width, height = resolution
    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi, constrained_layout=True)
    for index, row in enumerate(graph.edges.itertuples(index=False)):
        _draw_edge(
            ax,
            positions[str(row.source)],
            positions[str(row.target)],
            str(row.type),
            attributes.edge_colors[index],
            attributes.edge_widths[index],
            attributes.edge_alpha[index],
            bool(attributes.edge_reverse[index]),
        )
    points = np.asarray([positions[node] for node in graph.node_ids])
    node_rgba = attributes.node_colors.copy()
    node_rgba[:, 3] *= attributes.node_alpha
    ax.scatter(
        points[:, 0],
        points[:, 1],
        s=attributes.node_sizes,
        c=node_rgba,
        edgecolors="#20242a",
        linewidths=1.2,
        zorder=3,
    )
    labels_enabled = graph.node_count <= 100 if show_labels is None else show_labels
    if labels_enabled:
        for node, (x, y), alpha in zip(graph.node_ids, points, attributes.node_alpha, strict=True):
            if alpha > 0:
                ax.text(x, y, node, ha="center", va="center", fontsize=8, zorder=4)
    if title:
        ax.set_title(title)
    if event_labels:
        ax.text(
            0.01,
            0.01,
            " • ".join(event_labels),
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=9,
            bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#777"},
        )
    ax.set_aspect("equal")
    ax.axis("off")
    ax.margins(0.15)
    return fig, ax


def figure_rgb(fig: Figure) -> np.ndarray:
    fig.canvas.draw()
    canvas = fig.canvas
    if not isinstance(canvas, FigureCanvasAgg):
        raise TypeError("frame export requires the Matplotlib Agg canvas")
    return np.asarray(canvas.buffer_rgba())[..., :3].copy()  # type: ignore[no-untyped-call]


def save_static(fig: Figure, output: str | Path, dpi: int) -> Path:
    path = Path(output)
    if path.suffix.lower() not in {".png", ".svg", ".pdf"}:
        raise ValueError("static output must be PNG, SVG, or PDF")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, transparent=False)
    return path
