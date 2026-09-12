from pathlib import Path

from topopulse import DynamicNetwork
from topopulse.config import LayoutConfig, NetworkConfig

ROOT = Path(__file__).parent
positions = {"EGFR": (0, 4), "RAS": (0, 3), "RAF": (0, 2), "MEK": (0, 1), "ERK": (0, 0)}
network = DynamicNetwork.from_edgelist(
    ROOT / "data/mapk_network.csv",
    config=NetworkConfig(layout=LayoutConfig(name="fixed", positions=positions)),
)
network.plot(node_values=[1, 0.8, 0.6, 0.4, 0.2], output=ROOT / "../artifacts/custom_layout.svg")
network.save_layout(ROOT / "../artifacts/mapk_layout.json")
