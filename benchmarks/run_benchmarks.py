"""Run representative scales and write measured CSV/JSON results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from benchmark_core import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Skip the two largest scales")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/benchmarks"))
    args = parser.parse_args()
    scales = [(100, 1_000), (1_000, 10_000)]
    if not args.quick:
        scales.extend([(10_000, 100_000), (100_000, 1_000_000)])
    results = [run_benchmark(nodes, edges, frames=10) for nodes, edges in scales]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "benchmark.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(results).to_csv(args.output_dir / "benchmark.csv", index=False)


if __name__ == "__main__":
    main()
