from pathlib import Path

from topopulse import animate_difference
from topopulse.config import NetworkConfig, NodeStyle

ROOT = Path(__file__).parent
config = NetworkConfig(node_style=NodeStyle(normalization="symmetric", cmap="coolwarm"))
animate_difference(
    ROOT / "data/mapk_network.csv",
    reference=ROOT / "data/mapk_control.csv",
    comparison=ROOT / "data/mapk_inhibitor.csv",
    mode="difference",
    output=ROOT / "../artifacts/treatment_difference.mp4",
    config=config,
)
