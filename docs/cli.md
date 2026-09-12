# CLI

```bash
topopulse animate network.csv activity.csv --edge-data flux.csv --output pathway.mp4
topopulse plot network.csv --node-values state.csv --output state.svg
topopulse validate network.csv activity.csv
topopulse inspect network.csv
topopulse layout network.csv --layout spring --seed 42 --output layout.json
topopulse benchmark --nodes 1000 --edges 10000 --frames 100
```

Commands print machine-readable JSON where the output is a report.

