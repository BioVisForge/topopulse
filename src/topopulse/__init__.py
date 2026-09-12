"""TopoPulse: dynamic biological network visualization."""

from ._version import __version__
from .api import (
    DynamicNetwork,
    animate_conditions,
    animate_difference,
    animate_network,
    plot_network,
    validate_network,
)
from .config import (
    AnimationConfig,
    EdgeStyle,
    FilterConfig,
    LayoutConfig,
    NetworkConfig,
    NodeStyle,
    PerformanceConfig,
)
from .errors import *  # noqa: F403
from .graph import AlignmentReport, GraphData
from .results import AnimationResult

__all__ = [
    "AlignmentReport",
    "AnimationConfig",
    "AnimationResult",
    "DynamicNetwork",
    "EdgeStyle",
    "FilterConfig",
    "GraphData",
    "LayoutConfig",
    "NetworkConfig",
    "NodeStyle",
    "PerformanceConfig",
    "__version__",
    "animate_conditions",
    "animate_difference",
    "animate_network",
    "plot_network",
    "validate_network",
]
