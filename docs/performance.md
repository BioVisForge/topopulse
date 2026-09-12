# Performance

String-to-integer mapping, adjacency statistics, normalization, interpolation, differences,
top-activity selection, and chunk planning run in Rust. Substantial kernels release the GIL.
Layouts and final drawing remain Python-side.

Animation encoding streams one rendered frame at a time. Current CSV/pandas adapters materialize
the numeric table; NPY uses memory mapping at input but some alignment paths may still allocate a
contiguous copy. Use filtering before rendering very large networks.

Run `topopulse benchmark` for measured local timings. The repository contains no fabricated
performance table.

