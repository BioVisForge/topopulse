from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from topopulse.config import LayoutConfig, NetworkConfig, NodeStyle
from topopulse.graph import GraphData
from topopulse.layouts import calculate_layout, load_layout, save_layout


@pytest.mark.parametrize(
    "name",
    ["spring", "kamada_kawai", "circular", "shell", "spectral", "random", "grid", "hierarchical"],
)
def test_layout_algorithms(name: str, edges) -> None:
    positions = calculate_layout(GraphData(edges), LayoutConfig(name=name))
    assert set(positions) == {"A", "B", "C"}
    assert all(len(point) == 2 for point in positions.values())


def test_layout_reproducibility(edges) -> None:
    graph = GraphData(edges)
    assert calculate_layout(graph, LayoutConfig(name="spring", seed=7)) == calculate_layout(
        graph, LayoutConfig(name="spring", seed=7)
    )


def test_fixed_layout_and_validation(edges) -> None:
    graph = GraphData(edges)
    positions = {"A": (0, 0), "B": (1, 0), "C": (2, 0)}
    assert calculate_layout(graph, LayoutConfig(name="fixed", positions=positions)) == positions
    with pytest.raises(ValueError, match="missing nodes"):
        calculate_layout(graph, LayoutConfig(name="fixed", positions={"A": (0, 0)}))
    with pytest.raises(ValueError, match="requires positions"):
        calculate_layout(graph, LayoutConfig(name="fixed"))


def test_layout_roundtrip(tmp_path) -> None:
    path = save_layout({"A": (1.0, 2.0)}, tmp_path / "layout.json")
    assert load_layout(path) == {"A": (1.0, 2.0)}
    path.write_text(json.dumps({"A": [1]}))
    with pytest.raises(ValueError, match="two-value"):
        load_layout(path)


def test_config_yaml_and_toml(tmp_path) -> None:
    yaml = tmp_path / "config.yaml"
    toml = tmp_path / "config.toml"
    yaml.write_text("alignment: fill_missing\nlayout:\n  name: circular\n")
    toml.write_text('alignment = "intersection"\n[layout]\nname = "grid"\n')
    assert NetworkConfig.from_file(yaml).layout.name == "circular"
    assert NetworkConfig.from_file(toml).alignment == "intersection"
    with pytest.raises(ValueError, match="YAML or TOML"):
        NetworkConfig.from_file(tmp_path / "x.json")


def test_config_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        NodeStyle(normalization="fixed")
    with pytest.raises(ValidationError):
        NetworkConfig(unknown=True)
