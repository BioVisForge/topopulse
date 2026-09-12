from __future__ import annotations

import json

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from topopulse.errors import DuplicateNodeError, MissingNodeDataError, UnknownEdgeError
from topopulse.graph import GraphData
from topopulse.io import EdgeTemporalData


def test_dataframe_graph(edges: pd.DataFrame) -> None:
    graph = GraphData.from_any(edges)
    assert graph.node_ids == ("A", "B", "C")
    assert graph.edge_count == 3
    assert graph.inspect()["edge_types"] == {"activation": 1, "inhibition": 1, "association": 1}


def test_csv_tsv_and_graphml(tmp_path, edges: pd.DataFrame) -> None:
    csv = tmp_path / "network.csv"
    tsv = tmp_path / "network.tsv"
    graphml = tmp_path / "network.graphml"
    edges.to_csv(csv, index=False)
    edges.to_csv(tsv, sep="\t", index=False)
    nx.write_graphml(
        nx.from_pandas_edgelist(edges, edge_attr=True, create_using=nx.DiGraph), graphml
    )
    assert GraphData.from_any(csv).edge_count == 3
    assert GraphData.from_any(tsv).edge_count == 3
    assert GraphData.from_any(graphml).edge_count == 3


def test_networkx_dict_and_list_inputs(edges: pd.DataFrame) -> None:
    nx_graph = nx.from_pandas_edgelist(edges, edge_attr=True, create_using=nx.DiGraph)
    assert GraphData.from_any(nx_graph).directed
    assert GraphData.from_any({"edges": edges}).edge_count == 3
    assert GraphData.from_any([("A", "B", "activation")]).node_count == 2
    assert GraphData.from_any([{"source": "A", "target": "B"}]).edge_count == 1


def test_invalid_graph_inputs() -> None:
    with pytest.raises(ValueError, match="required columns"):
        GraphData(pd.DataFrame({"source": ["A"]}))
    with pytest.raises(ValueError, match="unsupported edge types"):
        GraphData(pd.DataFrame({"source": ["A"], "target": ["B"], "type": ["magic"]}))
    with pytest.raises(TypeError, match="unsupported network input"):
        GraphData.from_any(123)


def test_alignment_policies(edges: pd.DataFrame) -> None:
    graph = GraphData(edges)
    indices, report = graph.align_nodes(["C", "A", "B"], "strict")
    assert indices.tolist() == [1, 2, 0]
    assert report.matched == 3
    indices, report = graph.align_nodes(["A", "B"], "fill_missing")
    assert indices.tolist() == [0, 1, -1]
    assert report.missing == ("C",)


def test_strict_and_duplicate_alignment_errors(edges: pd.DataFrame) -> None:
    graph = GraphData(edges)
    with pytest.raises(MissingNodeDataError, match="strict alignment"):
        graph.align_nodes(["A", "B"], "strict")
    with pytest.raises(DuplicateNodeError, match="duplicate"):
        graph.align_nodes(["A", "A", "C"], "fill_missing")


def test_inspection_statistics() -> None:
    graph = GraphData.from_any([("A", "A"), ("A", "B"), ("A", "B"), ("C", "D")])
    report = graph.inspect()
    assert report["self_loops"] == 1
    assert report["duplicate_edges"] == 1
    assert report["connected_components"] == 2
    assert report["degree_max"] == 4
    json.dumps(report)


def test_edge_long_form_and_alignment(edges: pd.DataFrame) -> None:
    long = pd.DataFrame(
        {
            "time": [0, 0, 1, 1],
            "source": ["A", "B", "A", "B"],
            "target": ["B", "C", "B", "C"],
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )
    data = EdgeTemporalData.from_any(long).align_to_edges(GraphData(edges), "fill_missing")
    assert data.values.shape == (2, 3)
    assert data.values[:, 0].tolist() == [1.0, 3.0]
    assert data.alignment and data.alignment.missing == ("C|A",)


def test_edge_strict_unknown(edges: pd.DataFrame) -> None:
    data = EdgeTemporalData.from_any(pd.DataFrame({"time": [0], "A|X": [1.0]}))
    with pytest.raises(UnknownEdgeError):
        data.align_to_edges(GraphData(edges), "strict")


def test_edge_npy_adapter_and_duplicate_validation(tmp_path, edges: pd.DataFrame) -> None:
    path = tmp_path / "edge.npy"
    np.save(path, [[1.0, 2.0, 3.0]])
    labels = ["A|B", "B|C", "C|A"]
    assert EdgeTemporalData.from_any(path, labels=labels).values.shape == (1, 3)
    duplicate = EdgeTemporalData.from_any([[1.0, 2.0]], labels=["A|B", "A|B"])
    with pytest.raises(ValueError, match="unique"):
        duplicate.align_to_edges(GraphData(edges), "fill_missing")
    with pytest.raises(ValueError, match="unknown alignment policy"):
        EdgeTemporalData.from_any([[1.0]], labels=["A|B"]).align_to_edges(GraphData(edges), "loose")
