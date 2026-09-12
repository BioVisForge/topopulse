"""Python-first object and functional APIs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from . import _backend
from .animation import Event, animate
from .config import LayoutConfig, NetworkConfig
from .graph import GraphData
from .io import EdgeTemporalData
from .layouts import Positions, calculate_layout, load_layout, save_layout
from .rendering import frame_attributes, render_frame, save_static
from .results import AnimationResult
from .temporal import TemporalData, calculate_difference


class DynamicNetwork:
    def __init__(self, graph: GraphData, config: NetworkConfig | None = None) -> None:
        self.graph = graph
        self.config = config or NetworkConfig()
        self.positions: Positions | None = None

    @classmethod
    def from_edgelist(
        cls, network: Any, *, config: NetworkConfig | None = None, directed: bool = True
    ) -> DynamicNetwork:
        return cls(GraphData.from_any(network, directed=directed), config)

    def layout(self, config: LayoutConfig | None = None) -> Positions:
        chosen = config or self.config.layout
        if self.positions is None or chosen.dynamic:
            self.positions = calculate_layout(self.graph, chosen)
        return self.positions

    def save_layout(self, path: str | Path) -> Path:
        return save_layout(self.layout(), path)

    def load_layout(self, path: str | Path) -> Positions:
        self.positions = load_layout(path)
        missing = sorted(set(self.graph.node_ids) - set(self.positions))
        if missing:
            raise ValueError(f"saved layout missing network nodes: {', '.join(missing)}")
        return self.positions

    def _apply_filters(
        self,
        nodes: TemporalData,
        edges: EdgeTemporalData | None,
    ) -> tuple[GraphData, TemporalData, EdgeTemporalData | None, int, int]:
        filtering = self.config.filtering
        graph = self.graph
        node_indices: np.ndarray | None = None
        if graph.node_count > filtering.max_nodes:
            if filtering.node_filter == "none":
                raise ValueError(
                    f"network has {graph.node_count} nodes, above max_nodes={filtering.max_nodes}; "
                    "choose node_filter='top_activity', 'degree', or 'component'"
                )
            if filtering.node_filter == "top_activity":
                node_indices = np.asarray(
                    _backend.top_activity_indices(nodes.values, filtering.max_nodes)
                )
            elif filtering.node_filter == "degree":
                degrees = np.asarray(graph._rust.degrees())
                node_indices = np.sort(np.argsort(-degrees, kind="stable")[: filtering.max_nodes])
            else:
                labels = np.asarray(graph._rust.component_labels())
                largest = int(np.argmax(np.bincount(labels)))
                node_indices = np.flatnonzero(labels == largest)[: filtering.max_nodes]
        edge_scores = None
        if edges is not None:
            with np.errstate(all="ignore"):
                edge_scores = np.nanmax(np.abs(edges.values), axis=0)
        elif "weight" in graph.edges:
            edge_scores = graph.edges["weight"].to_numpy(dtype=float)
        if (
            node_indices is None
            and graph.edge_count <= filtering.max_edges
            and filtering.edge_threshold is None
            and filtering.top_k_edges is None
        ):
            return graph, nodes, edges, 0, 0
        edge_budget = min(filtering.max_edges, filtering.top_k_edges or filtering.max_edges)
        filtered_graph, node_map, edge_map = graph.filtered(
            node_indices=node_indices,
            max_edges=edge_budget,
            edge_scores=edge_scores,
            edge_threshold=filtering.edge_threshold,
        )
        filtered_nodes = TemporalData(
            nodes.values[:, node_map],
            nodes.times,
            filtered_graph.node_ids,
            nodes.display_labels,
            nodes.alignment,
        )
        filtered_edges = None
        if edges is not None:
            keys = tuple(
                filtered_graph.edges["source"].astype(str)
                + "|"
                + filtered_graph.edges["target"].astype(str)
            )
            filtered_edges = EdgeTemporalData(
                edges.values[:, edge_map],
                edges.times,
                keys,
                edges.display_labels,
                edges.alignment,
                keys,
            )
        return (
            filtered_graph,
            filtered_nodes,
            filtered_edges,
            graph.node_count - filtered_graph.node_count,
            graph.edge_count - filtered_graph.edge_count,
        )

    def validate(
        self, node_data: Any | None = None, edge_data: Any | None = None
    ) -> dict[str, Any]:
        report: dict[str, Any] = {"network": self.graph.inspect()}
        frames = 1
        if node_data is not None:
            nodes = TemporalData.from_any(node_data).align_to_nodes(
                self.graph, self.config.alignment
            )
            frames = len(nodes.times)
            report["node_data"] = {
                **(nodes.alignment.to_dict() if nodes.alignment else {}),
                "time_points": frames,
                "nan_values": int(np.isnan(nodes.values).sum()),
            }
        if edge_data is not None:
            edges = EdgeTemporalData.from_any(edge_data).align_to_edges(
                self.graph, self.config.alignment
            )
            frames = len(edges.times)
            report["edge_data"] = {
                **(edges.alignment.to_dict() if edges.alignment else {}),
                "time_points": frames,
                "nan_values": int(np.isnan(edges.values).sum()),
            }
        report["recommended_processing_mode"] = _backend.recommend_processing_mode(
            self.graph.node_count,
            self.graph.edge_count,
            frames,
            8,
            self.config.performance.memory_limit_mb * 1024 * 1024,
        )
        return report

    def plot(
        self,
        *,
        node_values: Any | None = None,
        edge_values: Any | None = None,
        output: str | Path | None = None,
        title: str | None = None,
    ) -> Any:
        node_temporal = (
            TemporalData.from_any(node_values, labels=list(self.graph.node_ids)).align_to_nodes(
                self.graph, self.config.alignment
            )
            if node_values is not None
            else None
        )
        edge_labels = list(
            self.graph.edges["source"].astype(str) + "|" + self.graph.edges["target"].astype(str)
        )
        edge_temporal = (
            EdgeTemporalData.from_any(edge_values, labels=edge_labels).align_to_edges(
                self.graph, self.config.alignment
            )
            if edge_values is not None
            else None
        )
        node_raw = node_temporal.values[0] if node_temporal else None
        edge_raw = edge_temporal.values[0] if edge_temporal else None
        node_normalized = (
            node_temporal.normalized(
                self.config.node_style.normalization, self.config.node_style.fixed_range
            )[0]
            if node_temporal
            else None
        )
        edge_normalized = (
            edge_temporal.normalized(
                self.config.edge_style.normalization, self.config.edge_style.fixed_range
            )[0]
            if edge_temporal
            else None
        )
        attrs = frame_attributes(
            self.graph,
            node_normalized,
            edge_normalized,
            node_raw,
            edge_raw,
            self.config.node_style,
            self.config.edge_style,
        )
        fig, _ = render_frame(
            self.graph,
            self.layout(),
            attrs,
            title=title,
            resolution=self.config.animation.resolution,
            dpi=self.config.animation.dpi,
        )
        if output:
            path = save_static(fig, output, self.config.animation.dpi)
            plt.close(fig)
            return path
        return fig

    def animate(
        self,
        *,
        node_data: Any,
        output: str | Path,
        edge_data: Any | None = None,
        events: list[Event] | None = None,
        node_labels: list[str] | None = None,
        edge_labels: list[str] | None = None,
        times: list[Any] | None = None,
    ) -> AnimationResult:
        inferred_node_labels = node_labels or (
            list(self.graph.node_ids) if isinstance(node_data, np.ndarray) else None
        )
        nodes = TemporalData.from_any(
            node_data, labels=inferred_node_labels, times=times
        ).align_to_nodes(self.graph, self.config.alignment)
        if edge_data is not None:
            inferred_edge_labels = edge_labels or (
                list(
                    self.graph.edges["source"].astype(str)
                    + "|"
                    + self.graph.edges["target"].astype(str)
                )
                if isinstance(edge_data, np.ndarray)
                else None
            )
            edges = EdgeTemporalData.from_any(
                edge_data, labels=inferred_edge_labels, times=times
            ).align_to_edges(self.graph, self.config.alignment)
        else:
            edges = None
        graph, nodes, edges, removed_nodes, removed_edges = self._apply_filters(nodes, edges)
        positions = (
            self.layout() if graph is self.graph else calculate_layout(graph, self.config.layout)
        )
        return animate(
            graph,
            nodes,
            edges,
            positions,
            output,
            self.config,
            events,
            filtered_nodes=removed_nodes,
            filtered_edges=removed_edges,
        )


def plot_network(
    network: Any,
    *,
    node_values: Any | None = None,
    edge_values: Any | None = None,
    output: str | Path | None = None,
    config: NetworkConfig | None = None,
    **kwargs: Any,
) -> Any:
    return DynamicNetwork.from_edgelist(network, config=config).plot(
        node_values=node_values, edge_values=edge_values, output=output, **kwargs
    )


def animate_network(
    network: Any,
    *,
    node_data: Any,
    output: str | Path,
    edge_data: Any | None = None,
    config: NetworkConfig | None = None,
    events: list[Event] | None = None,
    node_labels: list[str] | None = None,
    edge_labels: list[str] | None = None,
    times: list[Any] | None = None,
) -> AnimationResult:
    return DynamicNetwork.from_edgelist(network, config=config).animate(
        node_data=node_data,
        edge_data=edge_data,
        output=output,
        events=events,
        node_labels=node_labels,
        edge_labels=edge_labels,
        times=times,
    )


def animate_difference(
    network: Any,
    *,
    reference: Any,
    comparison: Any,
    output: str | Path,
    mode: str = "difference",
    edge_reference: Any | None = None,
    edge_comparison: Any | None = None,
    config: NetworkConfig | None = None,
) -> AnimationResult:
    dynamic = DynamicNetwork.from_edgelist(network, config=config)
    ref = TemporalData.from_any(reference).align_to_nodes(dynamic.graph, dynamic.config.alignment)
    comp = TemporalData.from_any(comparison).align_to_nodes(dynamic.graph, dynamic.config.alignment)
    node_diff = calculate_difference(ref, comp, mode)
    edge_diff: EdgeTemporalData | None = None
    if edge_reference is not None or edge_comparison is not None:
        if edge_reference is None or edge_comparison is None:
            raise ValueError("both edge_reference and edge_comparison are required")
        edge_ref = EdgeTemporalData.from_any(edge_reference).align_to_edges(
            dynamic.graph, dynamic.config.alignment
        )
        edge_comp = EdgeTemporalData.from_any(edge_comparison).align_to_edges(
            dynamic.graph, dynamic.config.alignment
        )
        diff = calculate_difference(edge_ref, edge_comp, mode)
        edge_diff = EdgeTemporalData(
            diff.values, diff.times, diff.entities, diff.display_labels, None, diff.entities
        )
    return animate(dynamic.graph, node_diff, edge_diff, dynamic.layout(), output, dynamic.config)


def animate_conditions(
    network: Any,
    data: Mapping[str, Any],
    *,
    output_dir: str | Path,
    conditions: list[str] | None = None,
    config: NetworkConfig | None = None,
) -> dict[str, AnimationResult]:
    selected = conditions or list(data)
    unknown = sorted(set(selected) - set(data))
    if unknown:
        raise KeyError(f"unknown conditions: {', '.join(unknown)}")
    dynamic = DynamicNetwork.from_edgelist(network, config=config)
    directory = Path(output_dir)
    return {
        condition: dynamic.animate(node_data=data[condition], output=directory / f"{condition}.mp4")
        for condition in selected
    }


def validate_network(
    network: Any,
    node_data: Any | None = None,
    edge_data: Any | None = None,
    *,
    config: NetworkConfig | None = None,
) -> dict[str, Any]:
    return DynamicNetwork.from_edgelist(network, config=config).validate(node_data, edge_data)
