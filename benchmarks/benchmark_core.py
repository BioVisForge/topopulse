"""Compatibility entry point for the packaged benchmark implementation."""

from __future__ import annotations

from topopulse.benchmarking import run_benchmark

if __name__ == "__main__":
    import json

    print(json.dumps(run_benchmark(), indent=2))
