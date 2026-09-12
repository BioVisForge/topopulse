#!/usr/bin/env bash
set -euo pipefail

uv run topopulse animate examples/data/mapk_network.csv examples/data/mapk_activity.csv \
  --edge-data examples/data/mapk_flux.csv --layout spring --node-normalization global \
  --fps 12 --output artifacts/pathway.mp4
