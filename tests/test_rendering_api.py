from __future__ import annotations

import json

import matplotlib.pyplot as plt
import numpy as np
import pytest

from topopulse import DynamicNetwork, plot_network, validate_network
from topopulse.config import EdgeStyle, FilterConfig, LayoutConfig, NetworkConfig, NodeStyle
from topopulse.rendering import frame_attributes


def test_frame_mappings_and_flux_direction(edges) -> None:
    graph = DynamicNetwork.from_edgelist(edges).graph
    config = NetworkConfig(
        node_style=NodeStyle(size_by="activity", opacity_by="confidence"),
        edge_style=EdgeStyle(
            width_by="flux",
            color_by="sign",
            opacity_by="confidence",
            normalization="symmetric",
            direction="flux",
        ),
    )
    attrs = frame_attributes(
        graph,
        np.array([0.0, 0.5, 1.0]),
        np.array([0.0, 0.5, 1.0]),
        np.array([0.0, np.nan, 1.0]),
        np.array([-1.0, 0.0, 1.0]),
        config.node_style,
        config.edge_style,
    )
    assert attrs.node_sizes[0] == config.node_style.size_range[0]
    assert attrs.node_sizes[-1] == config.node_style.size_range[1]
    assert attrs.edge_widths[0] == attrs.edge_widths[-1]
    assert attrs.edge_reverse.tolist() == [True, False, False]
    assert attrs.node_missing.tolist() == [False, True, False]


def test_direction_does_not_reverse_by_default(edges) -> None:
    graph = DynamicNetwork.from_edgelist(edges).graph
    style = EdgeStyle(direction="network")
    attrs = frame_attributes(
        graph, None, np.array([0.0, 0.5, 1.0]), None, np.array([-1.0, 0.0, 1.0]), NodeStyle(), style
    )
    assert not attrs.edge_reverse.any()


def test_static_outputs(tmp_path, edges) -> None:
    for suffix in ("png", "svg", "pdf"):
        output = tmp_path / f"network.{suffix}"
        assert plot_network(edges, node_values=[0.0, 0.5, 1.0], output=output) == output
        assert output.stat().st_size > 500


def test_plot_returns_figure(edges) -> None:
    figure = plot_network(edges, node_values=[0, 1, 2])
    assert figure.axes
    plt.close(figure)


def test_invalid_static_suffix(tmp_path, edges) -> None:
    with pytest.raises(ValueError, match="PNG, SVG, or PDF"):
        plot_network(edges, node_values=[0, 1, 2], output=tmp_path / "x.txt")


def test_validate_report(edges, nodes) -> None:
    report = validate_network(edges, nodes)
    assert report["network"]["nodes"] == 3
    assert report["node_data"]["time_points"] == 3
    assert report["node_data"]["nan_values"] == 1
    assert report["recommended_processing_mode"] == "in_memory"
    json.dumps(report)


def test_dynamic_network_layout_persistence(tmp_path, edges) -> None:
    engine = DynamicNetwork.from_edgelist(
        edges, config=NetworkConfig(layout=LayoutConfig(name="circular"))
    )
    first = engine.layout()
    assert first is engine.layout()
    path = engine.save_layout(tmp_path / "layout.json")
    second = DynamicNetwork.from_edgelist(edges)
    assert second.load_layout(path) == first


def test_large_network_budget_requires_policy(tmp_path) -> None:
    edges = [(f"N{i}", f"N{i + 1}") for i in range(5)]
    data = np.arange(12, dtype=float).reshape(2, 6)
    engine = DynamicNetwork.from_edgelist(
        edges, config=NetworkConfig(filtering=FilterConfig(max_nodes=3))
    )
    with pytest.raises(ValueError, match="choose node_filter"):
        engine.animate(node_data=data, output=tmp_path / "x.gif")


def test_top_activity_filter_is_reported(tmp_path) -> None:
    edges = [(f"N{i}", f"N{i + 1}") for i in range(5)]
    data = np.array([[9, 8, 7, 1, 0, 0], [9, 8, 7, 1, 0, 0]], dtype=float)
    config = NetworkConfig(
        filtering=FilterConfig(max_nodes=3, max_edges=2, node_filter="top_activity"),
        animation={"fps": 2, "resolution": (320, 240)},
    )
    result = DynamicNetwork.from_edgelist(edges, config=config).animate(
        node_data=data, output=tmp_path / "filtered.gif"
    )
    assert result.filtered_nodes == 3
    assert result.edge_count <= 2


@pytest.mark.parametrize("policy", ["degree", "component"])
def test_topology_filter_policies(tmp_path, policy: str) -> None:
    edges = [("A", "B"), ("B", "C"), ("D", "E")]
    data = np.ones((2, 5))
    config = NetworkConfig(
        filtering=FilterConfig(max_nodes=3, max_edges=3, node_filter=policy),
        animation={"fps": 2, "resolution": (320, 240)},
    )
    result = DynamicNetwork.from_edgelist(edges, config=config).animate(
        node_data=data, output=tmp_path / f"{policy}.gif"
    )
    assert result.node_count <= 3
    assert result.filtered_nodes >= 2


def test_filter_threshold_and_saved_layout_error(tmp_path, edges) -> None:
    graph = DynamicNetwork.from_edgelist(edges).graph
    filtered, _, edge_map = graph.filtered(
        max_edges=2, edge_scores=np.array([0.9, 0.2, 0.8]), edge_threshold=0.5
    )
    assert filtered.edge_count == 2
    assert edge_map.tolist() == [0, 2]
    with pytest.raises(ValueError, match="removed every edge"):
        graph.filtered(edge_scores=np.zeros(3), edge_threshold=1.0)
    layout = tmp_path / "missing.json"
    layout.write_text('{"A": [0, 0]}')
    with pytest.raises(ValueError, match="missing network nodes"):
        DynamicNetwork.from_edgelist(edges).load_layout(layout)
