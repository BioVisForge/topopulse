# Node data

Node data has shape `time × nodes`. CSV/TSV, NumPy, pandas, xarray, NPY, and NPZ are implemented.
NumPy data without embedded labels uses graph node order or explicit `node_labels`.

Alignment policies:

- `strict`: exact entity agreement; default.
- `intersection`: unmatched network entities remain missing.
- `fill_missing`: allocate missing network entities as NaN.

Actual times and display labels are stored separately. Numeric, categorical, and datetime-like
coordinates are supported; duplicates are rejected.

