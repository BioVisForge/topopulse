from pathlib import Path

from topopulse import animate_network
from topopulse.config import EdgeStyle, NetworkConfig

ROOT = Path(__file__).parent
config = NetworkConfig(
    edge_style=EdgeStyle(
        width_by="flux", color_by="sign", normalization="symmetric", direction="flux"
    )
)
animate_network(
    ROOT / "data/mapk_network.csv",
    node_data=ROOT / "data/mapk_activity.csv",
    edge_data=ROOT / "data/mapk_flux.csv",
    output=ROOT / "../artifacts/dynamic_edges.gif",
    config=config,
)
