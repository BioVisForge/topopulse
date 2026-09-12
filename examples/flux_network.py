from pathlib import Path

from topopulse import animate_network
from topopulse.config import EdgeStyle, NetworkConfig
from topopulse.datasets import flux_reversal

ROOT = Path(__file__).parent
network, nodes, flux = flux_reversal()
config = NetworkConfig(
    edge_style=EdgeStyle(direction="flux", normalization="symmetric", color_by="sign")
)
animate_network(
    network,
    node_data=nodes,
    edge_data=flux,
    output=ROOT / "../artifacts/flux_reversal.gif",
    config=config,
)
