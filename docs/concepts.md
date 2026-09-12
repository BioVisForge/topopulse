# Concepts

TopoPulse separates topology, temporal data, visual mappings, and rendering. Graph IDs are mapped
once to compact integers. A layout is computed once and reused across every frame. Node and edge
normalization are independent; animation defaults to global normalization so colors keep the same
meaning over time.

Missing values remain missing. Their visual policy is explicit: neutral, transparent, fixed color,
or hidden.

