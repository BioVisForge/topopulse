from pathlib import Path

from topopulse import DynamicNetwork
from topopulse.datasets import large_synthetic_network

ROOT = Path(__file__).parent
network, activity = large_synthetic_network(nodes=250, edges=1000, frames=3)
engine = DynamicNetwork.from_edgelist(network)
print(engine.validate(activity))
engine.plot(
    node_values=activity.iloc[0, 1:].to_numpy(), output=ROOT / "../artifacts/large_network.png"
)
