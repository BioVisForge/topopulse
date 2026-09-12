"""TopoPulse command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .api import DynamicNetwork
from .config import AnimationConfig, LayoutConfig, NetworkConfig, NodeStyle

app = typer.Typer(no_args_is_help=True, help="Dynamic biological network visualization.")


def _config(path: Path | None, layout: str | None = None) -> NetworkConfig:
    config = NetworkConfig.from_file(path) if path else NetworkConfig()
    if layout:
        config.layout = LayoutConfig(name=layout)
    return config


@app.command()
def animate(
    network: Annotated[Path, typer.Argument(exists=True, readable=True)],
    node_data: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")],
    edge_data: Annotated[Path | None, typer.Option("--edge-data")] = None,
    layout: Annotated[str, typer.Option()] = "spring",
    node_normalization: Annotated[str, typer.Option()] = "global",
    fps: Annotated[float, typer.Option()] = 12.0,
    config_file: Annotated[Path | None, typer.Option("--config")] = None,
) -> None:
    config = _config(config_file, layout)
    config.node_style = NodeStyle(normalization=node_normalization)
    config.animation = AnimationConfig(fps=fps)
    result = DynamicNetwork.from_edgelist(network, config=config).animate(
        node_data=node_data, edge_data=edge_data, output=output
    )
    typer.echo(json.dumps(result.to_dict(), indent=2))


@app.command()
def plot(
    network: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")],
    node_values: Annotated[Path | None, typer.Option("--node-values")] = None,
    layout: Annotated[str, typer.Option()] = "spring",
) -> None:
    result = DynamicNetwork.from_edgelist(network, config=_config(None, layout)).plot(
        node_values=node_values, output=output
    )
    typer.echo(str(result))


@app.command()
def validate(
    network: Annotated[Path, typer.Argument(exists=True, readable=True)],
    node_data: Annotated[Path | None, typer.Argument()] = None,
    edge_data: Annotated[Path | None, typer.Option("--edge-data")] = None,
) -> None:
    typer.echo(
        json.dumps(DynamicNetwork.from_edgelist(network).validate(node_data, edge_data), indent=2)
    )


@app.command()
def inspect(network: Annotated[Path, typer.Argument(exists=True, readable=True)]) -> None:
    typer.echo(json.dumps(DynamicNetwork.from_edgelist(network).graph.inspect(), indent=2))


@app.command("layout")
def layout_command(
    network: Annotated[Path, typer.Argument(exists=True, readable=True)],
    output: Annotated[Path, typer.Option("--output", "-o")] = Path("layout.json"),
    algorithm: Annotated[str, typer.Option("--layout")] = "spring",
    seed: Annotated[int, typer.Option()] = 42,
) -> None:
    config = NetworkConfig(layout=LayoutConfig(name=algorithm, seed=seed))
    typer.echo(str(DynamicNetwork.from_edgelist(network, config=config).save_layout(output)))


@app.command()
def benchmark(
    nodes: Annotated[int, typer.Option()] = 1000,
    edges: Annotated[int, typer.Option()] = 10000,
    frames: Annotated[int, typer.Option()] = 100,
) -> None:
    from .benchmarking import run_benchmark

    typer.echo(json.dumps(run_benchmark(nodes, edges, frames), indent=2))


if __name__ == "__main__":
    app()
