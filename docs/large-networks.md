# Large networks

Rendering every node, edge, and label stops being interpretable before ingestion becomes the main
problem. `FilterConfig` imposes explicit node and edge budgets and supports top activity, degree,
or largest-component selection plus edge thresholds and top-k limits.

Networks over the configured budget raise an actionable error when no policy is selected. Removed
counts are returned in `AnimationResult` and the full filter configuration is written to metadata.
Labels are suppressed automatically above 100 nodes.

Community-level aggregation and WebGL rendering are planned; they are not claimed in v0.1.

