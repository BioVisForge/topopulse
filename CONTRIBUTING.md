# Contributing

TopoPulse welcomes focused fixes, tested adapters, scientific validation, and measured performance work.

```bash
git clone https://github.com/BioVisForge/topopulse.git
cd topopulse
uv sync --all-extras
uv run maturin develop
uv run ruff check .
uv run mypy src
uv run pytest --cov=topopulse --cov-fail-under=90
cargo test
uv run zensical build
```

Keep heavy numeric and graph operations in Rust. Every new input adapter must document exact ID,
time, duplicate, and missing-data behavior. Do not change mathematical behavior without a small,
manually verifiable test. Benchmarks must report the runtime environment and measured values.

Open an issue before large API changes. Contributions are accepted under the MIT license.

