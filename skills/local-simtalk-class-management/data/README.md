# data/

This directory holds captured JSON envelopes from successful `class_ops.py`
runs. The dispatcher writes to `data/inheritance_map.json`-style files
when the caller passes `--output <path>` (to be added). For now, the
caller should redirect stdout to a file:

```bash
python3 scripts/class_ops.py --no-infobox inspect .MaterialFlow.Station > data/inspect-Station.json
```

Each file is a single JSON envelope (one JSON object per file).