"""Generate the first complete MAPK demonstration."""

from pathlib import Path

from topopulse import DynamicNetwork
from topopulse.animation import Event
from topopulse.config import AnimationConfig, EdgeStyle, LayoutConfig, NetworkConfig, NodeStyle

ROOT = Path(__file__).parents[1]
data = ROOT / "examples/data"
artifacts = ROOT / "artifacts"
config = NetworkConfig(
    node_style=NodeStyle(cmap="plasma", normalization="global", size_by="activity"),
    edge_style=EdgeStyle(
        width_by="flux", color_by="sign", cmap="coolwarm", normalization="symmetric"
    ),
    layout=LayoutConfig(name="hierarchical"),
    animation=AnimationConfig(fps=4, resolution=(960, 640), dpi=100),
)
network = DynamicNetwork.from_edgelist(data / "mapk_network.csv", config=config)
network.plot(
    node_values=data / "mapk_activity.csv",
    output=artifacts / "mapk.svg",
    title="MAPK-like signaling",
)
events = [Event(5, "EGFR stimulation"), Event(20, "negative feedback")]
network.animate(
    node_data=data / "mapk_activity.csv",
    edge_data=data / "mapk_flux.csv",
    events=events,
    output=artifacts / "mapk.gif",
)
network.animate(
    node_data=data / "mapk_activity.csv",
    edge_data=data / "mapk_flux.csv",
    events=events,
    output=artifacts / "mapk.mp4",
)
