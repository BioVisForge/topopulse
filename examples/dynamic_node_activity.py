from pathlib import Path

from topopulse import animate_network

ROOT = Path(__file__).parent
animate_network(
    ROOT / "data/mapk_network.csv",
    node_data=ROOT / "data/mapk_activity.csv",
    output=ROOT / "../artifacts/node_activity.gif",
)
