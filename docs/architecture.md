# Architecture

```mermaid
flowchart TD
    A["Graph + temporal inputs"] --> B["Python adapters"]
    B --> C["Rust indexed graph"]
    C --> D["Alignment + normalization"]
    D --> E["Stable layout + frame plan"]
    E --> F["Matplotlib renderer"]
    F --> G["PNG / SVG / PDF"]
    F --> H["Streaming GIF / MP4 / WebM"]
```

The FFI boundary passes contiguous numeric arrays and integer indices. Biological strings are
mapped once, not once per frame. NetworkX is an adapter and small-graph layout helper, not the
computational graph backend.

