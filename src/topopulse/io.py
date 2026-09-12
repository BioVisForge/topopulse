"""Input adapters for node and edge temporal data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .errors import TimeAlignmentError, UnknownEdgeError
from .graph import AlignmentReport, GraphData
from .temporal import TemporalData


@dataclass(frozen=True)
class EdgeTemporalData(TemporalData):
    edge_keys: tuple[str, ...] = ()

    @classmethod
    def from_any(
        cls, value: Any, *, labels: list[str] | None = None, times: list[Any] | None = None
    ) -> EdgeTemporalData:
        if isinstance(value, cls):
            return value
        if isinstance(value, (str, Path)):
            path = Path(value)
            if path.suffix.lower() in {".csv", ".tsv", ".tab"}:
                value = pd.read_csv(path, sep="\t" if path.suffix.lower() != ".csv" else ",")
            else:
                temporal = TemporalData.from_any(path, labels=labels, times=times)
                return cls(
                    temporal.values,
                    temporal.times,
                    temporal.entities,
                    temporal.display_labels,
                    None,
                    temporal.entities,
                )
        if isinstance(value, pd.DataFrame) and {"time", "source", "target", "value"}.issubset(
            value.columns
        ):
            frame = value.copy()
            frame["edge"] = frame["source"].astype(str) + "|" + frame["target"].astype(str)
            if frame.duplicated(["time", "edge"]).any():
                raise ValueError("edge long-form data contains duplicate time/source/target rows")
            pivot = frame.pivot(index="time", columns="edge", values="value").reset_index()
            temporal = TemporalData.from_any(pivot)
        else:
            temporal = TemporalData.from_any(value, labels=labels, times=times)
        return cls(
            temporal.values,
            temporal.times,
            temporal.entities,
            temporal.display_labels,
            None,
            temporal.entities,
        )

    def align_to_edges(self, graph: GraphData, policy: str = "strict") -> EdgeTemporalData:
        keys = tuple(graph.edges["source"].astype(str) + "|" + graph.edges["target"].astype(str))
        lookup = {key: index for index, key in enumerate(self.entities)}
        if len(lookup) != len(self.entities):
            raise ValueError("edge identifiers must be unique")
        missing = tuple(key for key in keys if key not in lookup)
        extra = tuple(key for key in self.entities if key not in set(keys))
        if policy == "strict" and (missing or extra):
            raise UnknownEdgeError(
                f"strict edge alignment failed; missing={list(missing)}; extra={list(extra)}"
            )
        if policy not in {"strict", "intersection", "fill_missing"}:
            raise ValueError(f"unknown alignment policy: {policy}")
        aligned = np.full((len(self.times), len(keys)), np.nan)
        for output_index, key in enumerate(keys):
            if key in lookup:
                aligned[:, output_index] = self.values[:, lookup[key]]
        report = AlignmentReport(
            len(keys), len(self.entities), len(keys) - len(missing), missing, extra, policy
        )
        return EdgeTemporalData(aligned, self.times, keys, self.display_labels, report, keys)


def ensure_matching_times(node_data: TemporalData, edge_data: EdgeTemporalData | None) -> None:
    if edge_data is not None and node_data.times != edge_data.times:
        raise TimeAlignmentError("node and edge data must have identical time coordinates")
