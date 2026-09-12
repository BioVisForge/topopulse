# TopoPulse 0.1.0 Engineering Report

Validation date: 2026-09-11

## 1–4. Identity and architecture

1. **Project name:** TopoPulse, in the BioVisForge ecosystem.
2. **Distribution / import / CLI / Rust crate:** `topopulse` / `topopulse` / `topopulse` / `topopulse`.
3. **Architecture:** typed Python orchestration and adapters feed a compact Rust graph indexed once
   from biological strings to integers. Rust performs validation, alignment, normalization,
   interpolation, differential transforms, filtering, components, statistics, and chunk planning
   while releasing the GIL for substantial kernels. Python computes a stable reusable layout and
   streams frames through Matplotlib and ImageIO/FFmpeg.
4. **Repository structure:** `src/topopulse/` contains the Python package, `rust/src/` the PyO3
   backend, `tests/` the Python/scientific suite, `benchmarks/` measured runners, `examples/`
   executable studies, `docs/` the Zensical site, `artifacts/` verified outputs, and `.github/`
   CI, documentation, release, benchmark, and security workflows.

## 5–13. Supported surface

5. **Graph inputs:** CSV, TSV, pandas DataFrame, NetworkX graphs, mapping/list input, and GraphML.
6. **Time-series inputs:** CSV, TSV, NumPy arrays, NPY, NPZ, pandas DataFrames, and xarray
   DataArrays; numeric, categorical, and datetime-like time coordinates are preserved separately
   from display labels.
7. **Node mappings:** color, size, and opacity from normalized values; fixed border styling;
   automatic or explicit labels; neutral, fixed-color, transparent, and hidden missing values.
8. **Edge mappings:** width, color, and opacity; activation arrows, inhibition bars, undirected
   lines, and directional reaction/transport/unknown edges; optional signed-flux reversal.
9. **Layouts:** spring, Kamada–Kawai, circular, shell, spectral, random, grid, hierarchical, fixed
   coordinates, seeded reproducibility, JSON save/load, and reuse across frames by default.
10. **Differential networks:** node and edge `difference`, `ratio`, `log2_fold_change`, and
    `percent_change`; multiple conditions emit separate synchronized outputs.
11. **Rust modules:** `graph`, `indexing`, `temporal`, `normalize`, `filter`, `stats`, `streaming`,
    `errors`, and `python` bindings.
12. **Python API:** `DynamicNetwork`, `plot_network`, `animate_network`, `animate_difference`,
    `animate_conditions`, and `validate_network`, plus typed configuration and `AnimationResult`.
13. **CLI:** `animate`, `plot`, `validate`, `inspect`, `layout`, and `benchmark`.

## 14–20. Verification

| Check | Result |
|---|---|
| Python tests | 79 passed, 0 failed |
| Python coverage | 94.00% branch-aware coverage (908 statements, 226 branches) |
| Rust tests | 14 passed, 0 failed; doc tests passed |
| Rust formatting | `cargo fmt --check` passed |
| Rust lint | `cargo clippy --all-targets --all-features -- -D warnings` passed |
| Python format/lint | Ruff format check and lint passed |
| Type checking | mypy strict: no issues in 17 source files |
| Documentation | Zensical clean build; no issues found |
| Package build | sdist, ABI3 CPython 3.11+ wheel, and manylinux wheel built |
| Wheel smoke test | Fresh environment import, CLI help, and packaged benchmark passed |

## 21. Generated examples

- `artifacts/mapk.gif`: 7 frames, 960×640, 50,089 bytes.
- `artifacts/mapk.mp4`: H.264, 7 frames, 960×640, 22,859 bytes.
- `artifacts/mapk.svg`: valid SVG, 16,690 bytes.
- `artifacts/control_vs_inhibitor.mp4`: H.264, 7 frames, 960×640, 16,343 bytes.
- Additional static, missing-data, flux-reversal, perturbation, condition, and large-network
  outputs are under `artifacts/` with reproducibility sidecars where applicable.
- All eleven Python examples and the CLI shell example completed successfully.

The square transparent logo and dark/light variants in `docs/assets/` were created with the
built-in image generator from an original brief combining directed biological nodes, a temporal
pulse, and an inhibitory feedback motif.

## 22. Measured computational benchmarks

Linux x86-64, Python 3.12.14, NumPy 2.3.5, nine logical CPUs. Times are observed wall-clock
seconds for Rust-backed compute plus the Python boundary; they do not measure rendering.

| Nodes / edges | Ingest | Align | Normalize | Filter | Components |
|---:|---:|---:|---:|---:|---:|
| 100 / 1,000 | 0.000384 | 0.000074 | 0.000095 | 0.000018 | 0.000034 |
| 1,000 / 10,000 | 0.003774 | 0.000499 | 0.000591 | 0.000123 | 0.000354 |
| 10,000 / 100,000 | 0.035783 | 0.005967 | 0.007932 | 0.001288 | 0.004682 |
| 100,000 / 1,000,000 | 0.488218 | 0.080631 | 0.118432 | 0.016023 | 0.086673 |

Raw JSON and CSV, including dataset generation and chunk-planning timings, are retained in
`artifacts/benchmarks/`.

## 23. Current limitations

- Interactive HTML, SBML, SBGN, CX/CX2, BioPAX, PEtab, SIF, and Neo4j/Cytoscape exports are adapter
  targets rather than claimed v0.1 support.
- Matplotlib rendering is intentionally bounded by filtering; directly drawing or labeling a
  100,000-node graph is neither attempted nor presented as scientifically useful.
- Frames are streamed to encoders, but CSV/pandas inputs are materialized and some aligned arrays
  require a contiguous copy. Community aggregation, group hulls, and compartment-constrained
  layouts remain future work.
- A node time-series currently supplies one scalar channel per node/frame; it can drive multiple
  encodings, but independent per-frame multi-attribute channels are not yet accepted in one call.
- Windows and macOS wheels are configured in release CI but were not executed on this Linux host.
- GitHub and PyPI publication were not performed; the repository and trusted-publishing workflow
  are ready for an authorized BioVisForge maintainer to publish.

## Reproduce

```bash
git clone https://github.com/BioVisForge/topopulse.git
cd topopulse
uv sync --all-extras
uv run maturin develop
uv run pytest
uv run topopulse --help
uv run zensical serve
```

Shortest MAPK animation:

```bash
uv run topopulse animate examples/data/mapk_network.csv examples/data/mapk_activity.csv \
  --edge-data examples/data/mapk_flux.csv --output mapk.mp4
```
