"""Reproducible layout calculation and persistence."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import networkx as nx
import numpy as np

from .config import LayoutConfig
from .graph import GraphData

Positions = dict[str, tuple[float, float]]
if TYPE_CHECKING:
    NxGraph = nx.Graph[str, dict[str, Any], dict[str, Any]]
    NxDiGraph = nx.DiGraph[str, dict[str, Any], dict[str, Any]]
else:
    NxGraph = Any
    NxDiGraph = Any


def _networkx_graph(graph: GraphData) -> NxGraph | NxDiGraph:
    nx_graph: NxGraph | NxDiGraph = nx.DiGraph() if graph.directed else nx.Graph()
    nx_graph.add_nodes_from(graph.node_ids)
    nx_graph.add_edges_from(zip(graph.edges["source"], graph.edges["target"], strict=True))
    return nx_graph


def calculate_layout(graph: GraphData, config: LayoutConfig) -> Positions:
    if config.positions is not None:
        missing = sorted(set(graph.node_ids) - set(config.positions))
        if missing:
            raise ValueError(f"fixed positions missing nodes: {', '.join(missing)}")
        return {
            node: (float(config.positions[node][0]), float(config.positions[node][1]))
            for node in graph.node_ids
        }
    nx_graph = _networkx_graph(graph)
    if config.name == "fixed":
        raise ValueError("layout='fixed' requires positions")
    if config.name == "grid":
        width = max(1, math.ceil(math.sqrt(graph.node_count)))
        return {
            node: (float(index % width), float(-(index // width)))
            for index, node in enumerate(graph.node_ids)
        }
    if config.name == "hierarchical":
        generations = (
            list(nx.topological_generations(cast(NxDiGraph, nx_graph)))
            if nx.is_directed_acyclic_graph(nx_graph)
            else [list(graph.node_ids)]
        )
        positions: Positions = {}
        for y, generation in enumerate(generations):
            offset = (len(generation) - 1) / 2
            positions.update(
                {
                    str(node): (float(x - offset), float(-y))
                    for x, node in enumerate(sorted(generation, key=str))
                }
            )
        return positions
    raw: Mapping[str, np.ndarray]
    if config.name == "spring":
        raw = nx.spring_layout(nx_graph, seed=config.seed)
    elif config.name == "kamada_kawai":
        raw = nx.kamada_kawai_layout(nx_graph)
    elif config.name == "circular":
        raw = nx.circular_layout(nx_graph)
    elif config.name == "shell":
        raw = nx.shell_layout(nx_graph)
    elif config.name == "spectral":
        raw = nx.spectral_layout(nx_graph)
    else:
        raw = nx.random_layout(nx_graph, seed=config.seed)
    return {str(node): (float(point[0]), float(point[1])) for node, point in raw.items()}


def save_layout(positions: Positions, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {node: list(point) for node, point in positions.items()}, indent=2, sort_keys=True
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def load_layout(path: str | Path) -> Positions:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("layout JSON must be an object mapping node IDs to [x, y]")
    result = {
        str(node): (float(point[0]), float(point[1]))
        for node, point in data.items()
        if isinstance(point, list) and len(point) == 2
    }
    if len(result) != len(data):
        raise ValueError("every layout entry must be a two-value coordinate")
    return result
