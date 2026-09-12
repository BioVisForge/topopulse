"""Typed public configuration models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

Normalization = Literal[
    "global",
    "per_frame",
    "fixed",
    "symmetric",
    "percentile",
    "zscore",
    "robust_zscore",
    "log",
    "log1p",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class NodeStyle(StrictModel):
    color_by: str | None = "value"
    size_by: str | None = None
    opacity_by: str | None = None
    border_width_by: str | None = None
    cmap: str = "viridis"
    normalization: Normalization = "global"
    fixed_range: tuple[float, float] | None = None
    percentile_range: tuple[float, float] = (0.02, 0.98)
    size_range: tuple[float, float] = (250.0, 1100.0)
    missing_policy: Literal["transparent", "neutral", "color", "hide"] = "neutral"
    missing_color: str = "#b8bec7"
    base_color: str = "#4c78a8"
    edgecolor: str = "#20242a"

    @model_validator(mode="after")
    def validate_fixed(self) -> NodeStyle:
        if self.normalization == "fixed" and self.fixed_range is None:
            raise ValueError("fixed normalization requires fixed_range")
        return self


class EdgeStyle(StrictModel):
    width_by: str | None = "value"
    color_by: str | None = None
    opacity_by: str | None = None
    cmap: str = "coolwarm"
    normalization: Normalization = "global"
    fixed_range: tuple[float, float] | None = None
    percentile_range: tuple[float, float] = (0.02, 0.98)
    width_range: tuple[float, float] = (0.5, 6.0)
    color: str = "#586069"
    activation_color: str = "#267a3d"
    inhibition_color: str = "#a92c2c"
    missing_policy: Literal["transparent", "neutral", "hide"] = "neutral"
    direction: Literal["network", "flux"] = "network"


class LayoutConfig(StrictModel):
    name: Literal[
        "spring",
        "kamada_kawai",
        "circular",
        "shell",
        "spectral",
        "random",
        "grid",
        "hierarchical",
        "fixed",
    ] = "spring"
    seed: int = 42
    positions: dict[str, tuple[float, float]] | None = None
    dynamic: bool = False


class AnimationConfig(StrictModel):
    fps: float = Field(default=12.0, gt=0)
    duration: float | None = Field(default=None, gt=0)
    loop: int = Field(default=0, ge=0)
    codec: str = "libx264"
    bitrate: str | None = None
    dpi: int = Field(default=120, gt=0)
    resolution: tuple[int, int] = (1280, 720)
    time_mode: Literal["uniform", "proportional", "custom"] = "uniform"
    custom_durations: list[float] | None = None
    emit_metadata: bool = True


class PerformanceConfig(StrictModel):
    mode: Literal["auto", "in_memory", "streaming"] = "auto"
    memory_limit_mb: int = Field(default=2048, gt=0)
    chunk_size: int = Field(default=32, gt=0)
    workers: int = Field(default=0, ge=0)


class FilterConfig(StrictModel):
    max_nodes: int = Field(default=5000, gt=0)
    max_edges: int = Field(default=20000, gt=0)
    node_filter: Literal["none", "top_activity", "degree", "component"] = "none"
    min_degree: int = Field(default=0, ge=0)
    edge_threshold: float | None = None
    top_k_edges: int | None = Field(default=None, gt=0)


class NetworkConfig(StrictModel):
    alignment: Literal["strict", "intersection", "fill_missing"] = "strict"
    directed: bool = True
    node_style: NodeStyle = Field(default_factory=NodeStyle)
    edge_style: EdgeStyle = Field(default_factory=EdgeStyle)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    animation: AnimationConfig = Field(default_factory=AnimationConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    filtering: FilterConfig = Field(default_factory=FilterConfig)

    @classmethod
    def from_file(cls, path: str | Path) -> NetworkConfig:
        path = Path(path)
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".toml":
            import tomllib

            data = tomllib.loads(path.read_text(encoding="utf-8"))
        else:
            raise ValueError("configuration must be YAML or TOML")
        return cls.model_validate(data)
