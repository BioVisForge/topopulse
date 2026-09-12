# Configuration

`NetworkConfig` contains `NodeStyle`, `EdgeStyle`, `LayoutConfig`, `AnimationConfig`,
`PerformanceConfig`, and `FilterConfig`. The same schema can be loaded from YAML or TOML.

```yaml
alignment: strict
node_style:
  color_by: activity
  normalization: global
edge_style:
  width_by: flux
  normalization: symmetric
layout:
  name: spring
  seed: 42
```

Visual colors belong in the style layer; computational kernels never hardcode a palette.

