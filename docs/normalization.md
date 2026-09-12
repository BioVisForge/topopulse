# Normalization

Rust implements global, per-frame, fixed, symmetric, percentile, z-score, robust z-score, log,
and log1p modes. Node and edge modes are configured independently.

Global normalization is the animation default. Per-frame scaling can make small late changes look
as strong as an early peak, so use it only when relative within-frame rank is the scientific goal.
`symmetric` places zero at the center of a diverging colormap. NaN is never replaced by zero.

