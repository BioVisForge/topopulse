"""Time-series adapters and Rust-backed transformation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xarray as xr

from . import _backend
from .errors import LabelMismatchError, TimeAlignmentError
from .graph import AlignmentReport, GraphData


@dataclass(frozen=True)
class TemporalData:
    values: np.ndarray
    times: tuple[Any, ...]
    entities: tuple[str, ...]
    display_labels: tuple[str, ...]
    alignment: AlignmentReport | None = None

    @classmethod
    def from_any(
        cls,
        value: Any,
        *,
        labels: list[str] | None = None,
        times: list[Any] | None = None,
    ) -> TemporalData:
        if isinstance(value, cls):
            return value
        if isinstance(value, (str, Path)):
            path = Path(value)
            suffix = path.suffix.lower()
            if suffix in {".csv", ".tsv", ".tab"}:
                return cls.from_any(
                    pd.read_csv(path, sep="\t" if suffix != ".csv" else ","),
                    labels=labels,
                    times=times,
                )
            if suffix == ".npy":
                return cls.from_any(np.load(path, mmap_mode="r"), labels=labels, times=times)
            if suffix == ".npz":
                with np.load(path, allow_pickle=False) as archive:
                    key = "values" if "values" in archive else archive.files[0]
                    return cls.from_any(archive[key], labels=labels, times=times)
            raise ValueError(f"unsupported time-series extension: {suffix}")
        if isinstance(value, pd.DataFrame):
            frame = value.copy()
            frame_times = frame.pop("time").tolist() if "time" in frame else frame.index.tolist()
            array = frame.to_numpy(dtype=np.float64, copy=True)
            entity_ids = [str(column) for column in frame.columns]
            return cls._build(array, labels or entity_ids, times or frame_times)
        if isinstance(value, xr.DataArray):
            array = np.asarray(value.values, dtype=np.float64)
            entity_dim = value.dims[-1]
            time_dim = value.dims[0]
            inferred_labels = (
                [str(item) for item in value.coords[entity_dim].values]
                if entity_dim in value.coords
                else None
            )
            inferred_times = (
                list(value.coords[time_dim].values) if time_dim in value.coords else None
            )
            return cls._build(array, labels or inferred_labels, times or inferred_times)
        return cls._build(np.asarray(value, dtype=np.float64), labels, times)

    @classmethod
    def _build(
        cls, array: np.ndarray, labels: list[str] | None, times: list[Any] | None
    ) -> TemporalData:
        if array.ndim == 1:
            array = array[None, :]
        if array.ndim != 2 or array.shape[0] == 0 or array.shape[1] == 0:
            raise ValueError("time-series data must have non-empty shape (time, entities)")
        if labels is None or len(labels) != array.shape[1]:
            received = 0 if labels is None else len(labels)
            raise LabelMismatchError(
                f"expected {array.shape[1]} entity labels, received {received}"
            )
        actual_times = list(range(array.shape[0])) if times is None else list(times)
        if len(actual_times) != array.shape[0]:
            raise TimeAlignmentError(
                f"expected {array.shape[0]} time labels, received {len(actual_times)}"
            )
        if len(set(map(str, actual_times))) != len(actual_times):
            raise TimeAlignmentError("time labels must be unique")
        return cls(
            np.ascontiguousarray(array),
            tuple(actual_times),
            tuple(map(str, labels)),
            tuple(map(str, actual_times)),
        )

    def align_to_nodes(self, graph: GraphData, policy: str = "strict") -> TemporalData:
        indices, report = graph.align_nodes(list(self.entities), policy)
        aligned = np.full((len(self.times), graph.node_count), np.nan, dtype=np.float64)
        valid = indices >= 0
        aligned[:, valid] = self.values[:, indices[valid]]
        if policy == "intersection":
            aligned[:, ~valid] = np.nan
        return TemporalData(aligned, self.times, graph.node_ids, self.display_labels, report)

    def normalized(
        self, mode: str = "global", params: tuple[float, float] | None = None
    ) -> np.ndarray:
        flat = np.asarray(
            _backend.normalize_matrix(self.values, mode, list(params) if params else None)
        )
        return flat.reshape(self.values.shape)


def calculate_difference(
    reference: TemporalData, comparison: TemporalData, mode: str = "difference"
) -> TemporalData:
    if reference.times != comparison.times or reference.entities != comparison.entities:
        raise TimeAlignmentError(
            "reference and comparison must have identical time and entity coordinates"
        )
    values = np.asarray(
        _backend.differential(reference.values.ravel(), comparison.values.ravel(), mode)
    ).reshape(reference.values.shape)
    return TemporalData(values, reference.times, reference.entities, reference.display_labels)
