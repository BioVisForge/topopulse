"""Graph model and alignment contracts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

from . import _backend
from .errors import DuplicateNodeError, MissingNodeDataError, UnknownNodeError

REQUIRED_EDGE_COLUMNS = ("source", "target")
EDGE_TYPES = {
    "activation",
    "inhibition",
    "undirected",
    "reaction",
    "transport",
    "association",
    "unknown",
}


@dataclass(frozen=True)
class AlignmentReport:
    network_nodes: int
    data_entities: int
    matched: int
    missing: tuple[str, ...]
    extra: tuple[str, ...]
    policy: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GraphData:
    """Compact Rust-indexed graph plus edge metadata."""

    def __init__(self, edges: pd.DataFrame, *, directed: bool = True) -> None:
        missing = [column for column in REQUIRED_EDGE_COLUMNS if column not in edges]
        if missing:
            raise ValueError(f"edge list is missing required columns: {', '.join(missing)}")
        clean = edges.copy()
        clean["source"] = clean["source"].astype(str)
        clean["target"] = clean["target"].astype(str)
        if "type" not in clean:
            clean["type"] = "unknown"
        clean["type"] = clean["type"].fillna("unknown").astype(str).str.lower()
        invalid = sorted(set(clean["type"]) - EDGE_TYPES)
        if invalid:
            raise ValueError(f"unsupported edge types: {', '.join(invalid)}")
        self.edges = clean.reset_index(drop=True)
        self._rust = _backend.IndexedGraph(
            self.edges["source"].tolist(),
            self.edges["target"].tolist(),
            self.edges["type"].tolist(),
            directed,
        )

    @property
    def node_ids(self) -> tuple[str, ...]:
        return tuple(self._rust.node_ids)

    @property
    def sources(self) -> np.ndarray:
        return np.asarray(self._rust.sources)

    @property
    def targets(self) -> np.ndarray:
        return np.asarray(self._rust.targets)

    @property
    def directed(self) -> bool:
        return bool(self._rust.directed)

    @property
    def node_count(self) -> int:
        return len(self.node_ids)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @classmethod
    def from_any(cls, value: Any, *, directed: bool = True) -> GraphData:
        if isinstance(value, cls):
            return value
        if isinstance(value, pd.DataFrame):
            return cls(value, directed=directed)
        if isinstance(value, nx.Graph):
            rows = []
            for source, target, attrs in value.edges(data=True):
                rows.append({"source": source, "target": target, **attrs})
            return cls(pd.DataFrame(rows), directed=value.is_directed())
        if isinstance(value, (str, Path)):
            path = Path(value)
            if path.suffix.lower() == ".graphml":
                return cls.from_any(nx.read_graphml(path))
            separator = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
            return cls(pd.read_csv(path, sep=separator), directed=directed)
        if isinstance(value, Mapping):
            if "edges" in value:
                return cls.from_any(value["edges"], directed=directed)
            return cls(pd.DataFrame(value), directed=directed)
        if isinstance(value, Iterable):
            rows = []
            for edge in value:
                if isinstance(edge, Mapping):
                    rows.append(dict(edge))
                else:
                    fields = list(edge)
                    rows.append(
                        {
                            "source": fields[0],
                            "target": fields[1],
                            "type": fields[2] if len(fields) > 2 else "unknown",
                        }
                    )
            return cls(pd.DataFrame(rows), directed=directed)
        raise TypeError(f"unsupported network input: {type(value).__name__}")

    def align_nodes(
        self, data_ids: list[str], policy: str = "strict"
    ) -> tuple[np.ndarray, AlignmentReport]:
        counts = Counter(data_ids)
        if len(counts) != len(data_ids):
            duplicates = sorted(item for item, count in counts.items() if count > 1)
            raise DuplicateNodeError(f"duplicate node-data columns: {', '.join(duplicates)}")
        try:
            indices, missing, extra = _backend.alignment_index(
                list(self.node_ids), data_ids, policy
            )
        except ValueError as error:
            message = str(error)
            if "missing" in message:
                raise MissingNodeDataError(message) from error
            raise UnknownNodeError(message) from error
        report = AlignmentReport(
            self.node_count,
            len(data_ids),
            self.node_count - len(missing),
            tuple(missing),
            tuple(extra),
            policy,
        )
        return np.asarray(indices, dtype=np.int64), report

    def inspect(self) -> dict[str, Any]:
        degrees = np.asarray(self._rust.degrees(), dtype=np.int64)
        components = np.asarray(self._rust.component_labels(), dtype=np.int64)
        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "directed": self.directed,
            "connected_components": int(components.max() + 1) if len(components) else 0,
            "degree_min": int(degrees.min()) if len(degrees) else 0,
            "degree_mean": float(degrees.mean()) if len(degrees) else 0.0,
            "degree_max": int(degrees.max()) if len(degrees) else 0,
            "isolated_nodes": int((degrees == 0).sum()),
            "self_loops": int((self.edges["source"] == self.edges["target"]).sum()),
            "duplicate_edges": int(self._rust.duplicate_count()),
            "edge_types": self.edges["type"].value_counts().to_dict(),
            "edge_metadata": [
                column for column in self.edges if column not in REQUIRED_EDGE_COLUMNS
            ],
        }

    def filtered(
        self,
        *,
        node_indices: np.ndarray | None = None,
        max_edges: int | None = None,
        edge_scores: np.ndarray | None = None,
        edge_threshold: float | None = None,
    ) -> tuple[GraphData, np.ndarray, np.ndarray]:
        """Build a compact subgraph and return original node/edge index mappings."""
        selected_nodes = (
            np.arange(self.node_count)
            if node_indices is None
            else np.asarray(node_indices, dtype=np.int64)
        )
        node_set = set(selected_nodes.tolist())
        edge_mask = np.asarray(
            [
                int(source) in node_set and int(target) in node_set
                for source, target in zip(self.sources, self.targets, strict=True)
            ]
        )
        if edge_scores is not None and edge_threshold is not None:
            edge_mask &= np.asarray(edge_scores) >= edge_threshold
        selected_edges = np.flatnonzero(edge_mask)
        if max_edges is not None and len(selected_edges) > max_edges:
            scores = (
                np.asarray(edge_scores)
                if edge_scores is not None
                else np.asarray(
                    self.edges.get("weight", pd.Series(np.ones(self.edge_count))), dtype=float
                )
            )
            ranked = selected_edges[
                np.argsort(
                    -np.nan_to_num(np.abs(scores[selected_edges]), nan=-np.inf), kind="stable"
                )
            ]
            selected_edges = np.sort(ranked[:max_edges])
        if len(selected_edges) == 0:
            raise ValueError("filtering removed every edge; loosen the node/edge filters")
        filtered_graph = GraphData(
            self.edges.iloc[selected_edges].reset_index(drop=True), directed=self.directed
        )
        original_lookup = {node: index for index, node in enumerate(self.node_ids)}
        mapped_nodes = np.asarray(
            [original_lookup[node] for node in filtered_graph.node_ids], dtype=np.int64
        )
        return filtered_graph, mapped_nodes, selected_edges
