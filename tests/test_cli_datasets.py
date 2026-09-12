from __future__ import annotations

import json

from typer.testing import CliRunner

from topopulse.cli import app
from topopulse.datasets import (
    branching_network,
    feedback_loop,
    flux_reversal,
    large_synthetic_network,
    missing_values,
    multiple_conditions,
)

runner = CliRunner()


def test_datasets_are_deterministic() -> None:
    assert feedback_loop()[0].shape[0] == 5
    assert branching_network()[0].shape[0] == 4
    assert flux_reversal()[2].iloc[1, 1] < 0
    assert missing_values()[1].isna().sum().sum() == 2
    assert set(multiple_conditions()[1]) == {"control", "mek_inhibitor"}
    first = large_synthetic_network(10, 20, 2, seed=3)
    second = large_synthetic_network(10, 20, 2, seed=3)
    assert first[0].equals(second[0]) and first[1].equals(second[1])


def test_invalid_large_dataset_sizes() -> None:
    try:
        large_synthetic_network(1, 1, 1)
    except ValueError as error:
        assert "nodes >= 2" in str(error)
    else:
        raise AssertionError("invalid size accepted")


def test_cli_inspect_validate_layout_plot(tmp_path, edges, nodes) -> None:
    network = tmp_path / "network.csv"
    activity = tmp_path / "activity.csv"
    edges.to_csv(network, index=False)
    nodes.to_csv(activity, index=False)
    inspect_result = runner.invoke(app, ["inspect", str(network)])
    assert inspect_result.exit_code == 0
    inspection = json.loads(inspect_result.stdout)
    assert inspection["nodes"] == 3
    assert inspection["isolated_nodes"] == 0
    validate_result = runner.invoke(app, ["validate", str(network), str(activity)])
    assert validate_result.exit_code == 0
    layout = tmp_path / "layout.json"
    assert (
        runner.invoke(
            app, ["layout", str(network), "--output", str(layout), "--layout", "grid"]
        ).exit_code
        == 0
    )
    static = tmp_path / "static.svg"
    assert (
        runner.invoke(
            app, ["plot", str(network), "--node-values", str(activity), "--output", str(static)]
        ).exit_code
        == 0
    )
    assert layout.exists() and static.exists()


def test_cli_animate(tmp_path, edges, nodes) -> None:
    network = tmp_path / "network.csv"
    activity = tmp_path / "activity.csv"
    output = tmp_path / "animation.gif"
    edges.to_csv(network, index=False)
    nodes.to_csv(activity, index=False)
    result = runner.invoke(
        app, ["animate", str(network), str(activity), "--output", str(output), "--fps", "2"]
    )
    assert result.exit_code == 0, result.output
    assert output.exists()


def test_cli_benchmark_runs_from_installed_package() -> None:
    result = runner.invoke(app, ["benchmark", "--nodes", "10", "--edges", "20", "--frames", "2"])
    assert result.exit_code == 0, result.output
    measured = json.loads(result.stdout)
    assert measured["nodes"] == 10
    assert measured["graph_ingestion_seconds"] >= 0
