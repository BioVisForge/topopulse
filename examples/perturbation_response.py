from pathlib import Path

from topopulse import DynamicNetwork
from topopulse.animation import Event

ROOT = Path(__file__).parent
DynamicNetwork.from_edgelist(ROOT / "data/mapk_network.csv").animate(
    node_data=ROOT / "data/mapk_activity.csv",
    events=[Event(5, "EGFR stimulation"), Event(20, "feedback onset")],
    output=ROOT / "../artifacts/perturbation.gif",
)
