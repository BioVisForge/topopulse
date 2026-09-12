from pathlib import Path

from topopulse import plot_network

ROOT = Path(__file__).parent
plot_network(
    ROOT / "data/mapk_network.csv",
    node_values=[0.2, 0.4, 0.7, 0.9, 1.0],
    output=ROOT / "../artifacts/basic.png",
)
