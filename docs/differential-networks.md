# Differential networks

`animate_difference` supports comparison minus reference, ratio, log2 fold change, and percent
change for nodes and optional edges.

```python
animate_difference(
    network,
    reference=control,
    comparison=drug,
    mode="difference",
    output="drug_minus_control.mp4",
)
```

Coordinates must agree exactly. Undefined ratios and log transforms remain NaN.

