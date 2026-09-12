# Perturbations

```python
from topopulse.animation import Event

events = [Event(time=10, label="EGFR inhibitor"), Event(time=30, label="washout")]
network.animate(node_data=data, events=events, output="response.mp4")
```

Events annotate the matching frame. They do not alter the data or imply that the event caused the
subsequent state.

