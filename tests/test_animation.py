from __future__ import annotations

import json

import imageio.v2 as imageio
import pandas as pd
import pytest

from topopulse import (
    animate_conditions,
    animate_difference,
    animate_network,
    validate_network,
)
from topopulse.animation import Event
from topopulse.config import AnimationConfig, NetworkConfig, NodeStyle
from topopulse.errors import RenderingError, TimeAlignmentError


def small_config(**kwargs) -> NetworkConfig:
    animation_keys = {"time_mode", "custom_durations", "emit_metadata"}
    animation_kwargs = {key: value for key, value in kwargs.items() if key in animation_keys}
    network_kwargs = {key: value for key, value in kwargs.items() if key not in animation_keys}
    return NetworkConfig(
        animation=AnimationConfig(fps=2, resolution=(320, 240), dpi=80, **animation_kwargs),
        **network_kwargs,
    )


def test_gif_streaming_and_metadata(tmp_path, edges, nodes) -> None:
    output = tmp_path / "network.gif"
    result = animate_network(
        edges, node_data=nodes, output=output, config=small_config(), events=[Event(2, "treatment")]
    )
    assert result.frame_count == 3
    assert output.stat().st_size > 1000
    assert result.metadata_path and result.metadata_path.exists()
    metadata = json.loads(result.metadata_path.read_text())
    assert metadata["network_sha256"]
    assert metadata["time_points"] == ["0", "2", "5"]
    assert result.to_dict()["output_path"] == str(output)
    assert len(imageio.mimread(output)) == 3


@pytest.mark.ffmpeg
def test_mp4_output(tmp_path, edges, nodes) -> None:
    output = tmp_path / "network.mp4"
    result = animate_network(edges, node_data=nodes.fillna(0), output=output, config=small_config())
    assert result.frame_count == 3
    assert output.stat().st_size > 1000


def test_proportional_and_custom_timing(tmp_path, edges, nodes) -> None:
    proportional = animate_network(
        edges,
        node_data=nodes.fillna(0),
        output=tmp_path / "p.gif",
        config=small_config(time_mode="proportional"),
    )
    assert proportional.frame_count == 4
    custom = animate_network(
        edges,
        node_data=nodes.fillna(0),
        output=tmp_path / "c.gif",
        config=small_config(time_mode="custom", custom_durations=[0.5, 1.0, 0.5]),
    )
    assert custom.frame_count == 4


def test_invalid_custom_timing(tmp_path, edges, nodes) -> None:
    with pytest.raises(ValueError, match="one custom duration"):
        animate_network(
            edges,
            node_data=nodes,
            output=tmp_path / "x.gif",
            config=small_config(time_mode="custom", custom_durations=[1.0]),
        )


def test_differential_animation(tmp_path, edges, nodes) -> None:
    comparison = nodes.fillna(0).copy()
    comparison[["A", "B", "C"]] += 1
    output = tmp_path / "difference.gif"
    result = animate_difference(
        edges,
        reference=nodes.fillna(0),
        comparison=comparison,
        output=output,
        config=small_config(node_style=NodeStyle(normalization="symmetric")),
    )
    assert result.frame_count == 3


def test_node_edge_time_mismatch(tmp_path, edges, nodes) -> None:
    edge_data = pd.DataFrame({"time": [0, 1], "A|B": [1, 2], "B|C": [1, 2], "C|A": [1, 2]})
    with pytest.raises(TimeAlignmentError):
        animate_network(
            edges,
            node_data=nodes,
            edge_data=edge_data,
            output=tmp_path / "x.gif",
            config=small_config(),
        )


def test_invalid_animation_suffix(tmp_path, edges, nodes) -> None:
    with pytest.raises(ValueError, match="GIF, MP4, or WebM"):
        animate_network(edges, node_data=nodes, output=tmp_path / "x.avi", config=small_config())


def test_missing_ffmpeg_error(monkeypatch, tmp_path, edges, nodes) -> None:
    monkeypatch.setattr("topopulse.animation.shutil.which", lambda _: None)
    with pytest.raises(RenderingError, match="FFmpeg"):
        animate_network(edges, node_data=nodes, output=tmp_path / "x.mp4", config=small_config())


def test_dynamic_edges_validation_and_difference(tmp_path, edges, nodes) -> None:
    edge_values = pd.DataFrame(
        {
            "time": [0, 2, 5],
            "A|B": [1.0, 0.5, 0.2],
            "B|C": [0.2, 0.5, 1.0],
            "C|A": [0.0, 0.1, 0.2],
        }
    )
    report = validate_network(edges, nodes, edge_values)
    assert report["edge_data"]["matched"] == 3
    comparison_edges = edge_values.copy()
    comparison_edges.iloc[:, 1:] += 1.0
    comparison_nodes = nodes.fillna(0).copy()
    comparison_nodes[["A", "B", "C"]] += 1.0
    result = animate_difference(
        edges,
        reference=nodes.fillna(0),
        comparison=comparison_nodes,
        edge_reference=edge_values,
        edge_comparison=comparison_edges,
        output=tmp_path / "edge_difference.gif",
        config=small_config(),
    )
    assert result.edge_count == 3
    with pytest.raises(ValueError, match="both edge_reference"):
        animate_difference(
            edges,
            reference=nodes.fillna(0),
            comparison=nodes.fillna(0),
            edge_reference=edge_values,
            output=tmp_path / "invalid.gif",
            config=small_config(),
        )


@pytest.mark.ffmpeg
def test_conditions_and_unknown_selection(tmp_path, edges, nodes) -> None:
    results = animate_conditions(
        edges,
        {"control": nodes.fillna(0), "drug": nodes.fillna(0)},
        conditions=["drug"],
        output_dir=tmp_path,
        config=small_config(),
    )
    assert list(results) == ["drug"]
    with pytest.raises(KeyError, match="unknown conditions"):
        animate_conditions(edges, {"control": nodes}, conditions=["missing"], output_dir=tmp_path)
