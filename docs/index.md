# TopoPulse

![TopoPulse logo](assets/logo.png){ width="180" }

TopoPulse converts a biological network plus time-resolved node and optional edge data into
static figures and streaming animations. Scientific users work in Python or through one CLI;
Rust handles indexing, alignment, normalization, filtering, and temporal transformations.

```bash
topopulse animate network.csv activity.csv --output signaling.mp4
```

TopoPulse visualizes model or measurement state. It does not infer networks, simulate biology,
or turn visual thickness into evidence of causality.

