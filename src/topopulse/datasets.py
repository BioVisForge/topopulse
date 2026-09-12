"""Deterministic biological example datasets used by docs and tests."""

from __future__ import annotations

import numpy as np
import pandas as pd


def linear_signaling() -> tuple[pd.DataFrame, pd.DataFrame]:
    edges = pd.DataFrame(
        {
            "source": ["EGFR", "RAS", "RAF", "MEK"],
            "target": ["RAS", "RAF", "MEK", "ERK"],
            "type": ["activation"] * 4,
        }
    )
    activity = pd.DataFrame(
        {
            "time": [0, 5, 10, 15, 20],
            "EGFR": [0.1, 1.0, 0.7, 0.3, 0.1],
            "RAS": [0.0, 0.5, 1.0, 0.7, 0.2],
            "RAF": [0.0, 0.2, 0.7, 1.0, 0.5],
            "MEK": [0.0, 0.1, 0.4, 0.8, 1.0],
            "ERK": [0.0, 0.0, 0.2, 0.6, 1.0],
        }
    )
    return edges, activity


def feedback_loop() -> tuple[pd.DataFrame, pd.DataFrame]:
    edges, activity = linear_signaling()
    feedback = pd.DataFrame(
        [{"source": "ERK", "target": "RAF", "type": "inhibition", "weight": 0.7}]
    )
    return pd.concat([edges, feedback], ignore_index=True), activity


def branching_network() -> tuple[pd.DataFrame, pd.DataFrame]:
    edges = pd.DataFrame(
        {
            "source": ["EGFR", "EGFR", "RAS", "PI3K"],
            "target": ["RAS", "PI3K", "ERK", "AKT"],
            "type": ["activation"] * 4,
        }
    )
    values = pd.DataFrame(
        {
            "time": [0, 5, 10],
            "EGFR": [0, 1, 0.5],
            "RAS": [0, 0.7, 1],
            "PI3K": [0, 0.4, 0.9],
            "ERK": [0, 0.2, 0.8],
            "AKT": [0, 0.1, 0.7],
        }
    )
    return edges, values


def inhibitory_network() -> tuple[pd.DataFrame, pd.DataFrame]:
    edges, values = feedback_loop()
    return edges[edges["type"].isin(["activation", "inhibition"])], values


def flux_reversal() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    edges = pd.DataFrame(
        {"source": ["A", "B"], "target": ["B", "C"], "type": ["reaction", "transport"]}
    )
    nodes = pd.DataFrame(
        {"time": [0, 1, 2], "A": [1, 0.5, 0.2], "B": [0, 0.5, 0.8], "C": [0, 0.2, 1]}
    )
    flux = pd.DataFrame({"time": [0, 1, 2], "A|B": [1.0, -0.5, -1.0], "B|C": [0.2, 0.7, 1.0]})
    return edges, nodes, flux


def missing_values() -> tuple[pd.DataFrame, pd.DataFrame]:
    edges, values = linear_signaling()
    values.loc[1, "RAF"] = np.nan
    values.loc[3, "ERK"] = np.nan
    return edges, values


def multiple_conditions() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    edges, control = feedback_loop()
    inhibitor = control.copy()
    inhibitor[["MEK", "ERK"]] *= 0.2
    return edges, {"control": control, "mek_inhibitor": inhibitor}


def large_synthetic_network(
    nodes: int = 10_000, edges: int = 100_000, frames: int = 10, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if nodes < 2 or edges < 1 or frames < 1:
        raise ValueError("nodes >= 2, edges >= 1, and frames >= 1 are required")
    rng = np.random.default_rng(seed)
    source = rng.integers(0, nodes, edges)
    target = rng.integers(0, nodes, edges)
    target[target == source] = (target[target == source] + 1) % nodes
    names = np.asarray([f"N{index}" for index in range(nodes)])
    edge_frame = pd.DataFrame({"source": names[source], "target": names[target], "type": "unknown"})
    activity = pd.DataFrame(rng.normal(size=(frames, nodes)), columns=names)
    activity.insert(0, "time", np.arange(frames))
    return edge_frame, activity
