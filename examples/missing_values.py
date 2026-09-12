from pathlib import Path

from topopulse import animate_network
from topopulse.datasets import missing_values

ROOT = Path(__file__).parent
network, activity = missing_values()
animate_network(network, node_data=activity, output=ROOT / "../artifacts/missing.gif")
