from __future__ import annotations

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")


@pytest.fixture
def edges() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source": ["A", "B", "C"],
            "target": ["B", "C", "A"],
            "type": ["activation", "inhibition", "association"],
            "weight": [1.0, 0.5, 0.2],
        }
    )


@pytest.fixture
def nodes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "time": [0, 2, 5],
            "A": [0.0, 0.5, 1.0],
            "B": [1.0, 0.5, 0.0],
            "C": [0.2, float("nan"), 0.8],
        }
    )
