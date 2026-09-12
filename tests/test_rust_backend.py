from __future__ import annotations

import numpy as np
import pytest

from topopulse import _backend


def test_indexed_graph_properties() -> None:
    graph = _backend.IndexedGraph(["A", "B"], ["B", "C"], ["activation", "inhibition"], True)
    assert graph.node_ids == ["A", "B", "C"]
    assert graph.sources.tolist() == [0, 1]
    assert graph.targets.tolist() == [1, 2]
    assert graph.edge_types == ["activation", "inhibition"]
    assert graph.directed is True


def test_indexed_graph_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="equal length"):
        _backend.IndexedGraph(["A"], [], None, True)


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("global", [[0.0, 1 / 3], [2 / 3, 1.0]]),
        ("per_frame", [[0.0, 1.0], [0.0, 1.0]]),
        ("fixed", [[0.0, 0.25], [0.5, 0.75]]),
        ("symmetric", [[0.5, 2 / 3], [5 / 6, 1.0]]),
    ],
)
def test_normalization_modes(mode: str, expected: list[list[float]]) -> None:
    params = [0.0, 4.0] if mode == "fixed" else None
    result = np.asarray(
        _backend.normalize_matrix(np.array([[0.0, 1.0], [2.0, 3.0]]), mode, params)
    ).reshape(2, 2)
    np.testing.assert_allclose(result, expected)


def test_normalization_preserves_nan() -> None:
    result = np.asarray(_backend.normalize_matrix(np.array([[0.0, np.nan, 1.0]]), "global", None))
    assert np.isnan(result[1])


def test_zscore_and_robust_zscore() -> None:
    values = np.array([[1.0, 2.0, 3.0]])
    zscore = np.asarray(_backend.normalize_matrix(values, "zscore", None))
    robust = np.asarray(_backend.normalize_matrix(values, "robust_zscore", None))
    assert zscore[1] == pytest.approx(0.0)
    assert robust.tolist() == [-1.0, 0.0, 1.0]


def test_log_transforms_invalid_values_to_nan() -> None:
    log = np.asarray(_backend.normalize_matrix(np.array([[-1.0, 1.0]]), "log", None))
    log1p = np.asarray(_backend.normalize_matrix(np.array([[-2.0, 0.0]]), "log1p", None))
    assert np.isnan(log[0]) and log[1] == 0.0
    assert np.isnan(log1p[0]) and log1p[1] == 0.0


def test_percentile_clips_outlier() -> None:
    result = np.asarray(
        _backend.normalize_matrix(np.array([[0.0, 1.0, 100.0]]), "percentile", [0.0, 0.5])
    )
    assert result.tolist() == [0.0, 1.0, 1.0]


def test_fixed_requires_valid_range() -> None:
    with pytest.raises(ValueError, match="min < max"):
        _backend.normalize_matrix(np.array([[1.0]]), "fixed", [1.0, 1.0])


def test_interpolation() -> None:
    result = np.asarray(_backend.interpolate_matrix(np.array([[0.0, 2.0], [2.0, 4.0]]), 2)).reshape(
        3, 2
    )
    np.testing.assert_allclose(result, [[0, 2], [1, 3], [2, 4]])


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("difference", [1.0, -1.0]),
        ("ratio", [2.0, 0.5]),
        ("log2_fold_change", [1.0, -1.0]),
        ("percent_change", [100.0, -50.0]),
    ],
)
def test_differential_modes(mode: str, expected: list[float]) -> None:
    result = _backend.differential(np.array([1.0, 2.0]), np.array([2.0, 1.0]), mode)
    np.testing.assert_allclose(result, expected)


def test_top_activity_and_chunk_ranges() -> None:
    values = np.array([[1.0, 5.0, 0.0], [2.0, 1.0, 9.0]])
    assert _backend.top_activity_indices(values, 2) == [1, 2]
    assert _backend.chunk_ranges(5, 2) == [(0, 2), (2, 4), (4, 5)]


def test_processing_mode_recommendation() -> None:
    assert _backend.recommend_processing_mode(10, 10, 5, 8, 1_000_000) == "in_memory"
    assert (
        _backend.recommend_processing_mode(100_000, 1_000_001, 5, 8, 1_000_000_000) == "streaming"
    )
