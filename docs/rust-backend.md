# Rust backend

`graph.rs` owns compact indexing, degrees, components, and duplicate detection. `indexing.rs`
defines explicit entity alignment. `normalize.rs` implements numeric transformations while
preserving NaN. `temporal.rs` handles interpolation and differential transforms. `filter.rs`,
`stats.rs`, and `streaming.rs` cover selection, processing-mode estimates, and chunk boundaries.
`python.rs` is the only PyO3 exposure layer.

Rust tests validate mapping, topology, duplicates, normalization, missing values, interpolation,
differences, filtering, processing recommendations, and chunk boundaries.

