"""Generate treatment and difference demonstrations."""

from pathlib import Path

from topopulse import animate_conditions, animate_difference
from topopulse.config import AnimationConfig, NetworkConfig, NodeStyle

ROOT = Path(__file__).parents[1]
data = ROOT / "examples/data"
config = NetworkConfig(
    node_style=NodeStyle(normalization="symmetric", cmap="coolwarm"),
    animation=AnimationConfig(fps=4, resolution=(960, 640)),
)
animate_conditions(
    data / "mapk_network.csv",
    {"control": data / "mapk_control.csv", "mek_inhibitor": data / "mapk_inhibitor.csv"},
    output_dir=ROOT / "artifacts/conditions",
    config=config,
)
animate_difference(
    data / "mapk_network.csv",
    reference=data / "mapk_control.csv",
    comparison=data / "mapk_inhibitor.csv",
    output=ROOT / "artifacts/control_vs_inhibitor.mp4",
    config=config,
)
