from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from topopulse.errors import LabelMismatchError, TimeAlignmentError
from topopulse.graph import GraphData
from topopulse.temporal import TemporalData, calculate_difference


def test_dataframe_and_array_adapters(nodes: pd.DataFrame) -> None:
    data = TemporalData.from_any(nodes)
    assert data.times == (0, 2, 5)
    assert data.entities == ("A", "B", "C")
    array = TemporalData.from_any(np.ones((2, 3)), labels=["A", "B", "C"], times=["early", "late"])
    assert array.display_labels == ("early", "late")


def test_xarray_adapter() -> None:
    array = xr.DataArray(
        np.ones((2, 2)), dims=("time", "node"), coords={"time": [0, 3], "node": ["A", "B"]}
    )
    data = TemporalData.from_any(array)
    assert data.times == (0, 3)
    assert data.entities == ("A", "B")


def test_file_adapters(tmp_path, nodes: pd.DataFrame) -> None:
    csv = tmp_path / "nodes.csv"
    tsv = tmp_path / "nodes.tsv"
    npy = tmp_path / "nodes.npy"
    npz = tmp_path / "nodes.npz"
    nodes.to_csv(csv, index=False)
    nodes.to_csv(tsv, sep="\t", index=False)
    np.save(npy, nodes.iloc[:, 1:].to_numpy())
    np.savez(npz, values=nodes.iloc[:, 1:].to_numpy())
    assert TemporalData.from_any(csv).values.shape == (3, 3)
    assert TemporalData.from_any(tsv).values.shape == (3, 3)
    assert TemporalData.from_any(npy, labels=["A", "B", "C"]).values.shape == (3, 3)
    assert TemporalData.from_any(npz, labels=["A", "B", "C"]).values.shape == (3, 3)


def test_alignment_reorders_and_fills(nodes: pd.DataFrame) -> None:
    graph = GraphData.from_any([("C", "A"), ("A", "D")])
    data = TemporalData.from_any(nodes).align_to_nodes(graph, "fill_missing")
    assert data.entities == ("C", "A", "D")
    assert data.values[0, :2].tolist() == [0.2, 0.0]
    assert np.isnan(data.values[:, 2]).all()


def test_normalization_scientific_behavior() -> None:
    data = TemporalData.from_any(np.array([[0.0, 1.0], [10.0, 20.0]]), labels=["A", "B"])
    global_values = data.normalized("global")
    frame_values = data.normalized("per_frame")
    assert global_values[1, 0] == 0.5
    assert frame_values[1, 0] == 0.0


def test_missing_values_remain_missing(nodes: pd.DataFrame) -> None:
    result = TemporalData.from_any(nodes).normalized("global")
    assert np.isnan(result[1, 2])


def test_difference_validation_and_math(nodes: pd.DataFrame) -> None:
    reference = TemporalData.from_any(nodes.fillna(0))
    comparison_frame = nodes.fillna(0).copy()
    comparison_frame[["A", "B", "C"]] += 1.0
    comparison = TemporalData.from_any(comparison_frame)
    result = calculate_difference(reference, comparison)
    np.testing.assert_allclose(result.values, 1.0)
    with pytest.raises(TimeAlignmentError):
        calculate_difference(reference, TemporalData.from_any(comparison_frame.iloc[:-1]))


@pytest.mark.parametrize(
    ("array", "labels", "times", "error"),
    [
        (np.ones((2, 2)), ["A"], None, LabelMismatchError),
        (np.ones((2, 2)), ["A", "B"], [0], TimeAlignmentError),
        (np.ones((2, 2)), ["A", "B"], [0, 0], TimeAlignmentError),
        (np.empty((0, 2)), ["A", "B"], None, ValueError),
    ],
)
def test_invalid_temporal_inputs(array, labels, times, error) -> None:
    with pytest.raises(error):
        TemporalData.from_any(array, labels=labels, times=times)
