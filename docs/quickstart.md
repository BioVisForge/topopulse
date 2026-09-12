# Quickstart

```python
from topopulse import DynamicNetwork

network = DynamicNetwork.from_edgelist("network.csv")
result = network.animate(node_data="activity.csv", output="signaling.mp4")
print(result.to_dict())
```

The edge list needs `source` and `target`; `type` is optional. The activity table uses one `time`
column and one column per network node. Alignment defaults to `strict`, so missing or extra IDs
raise an error instead of disappearing.

