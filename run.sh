#!/usr/bin/env bash
# Presage scoring entry point.
#
# Usage: ./run.sh [DATA_DIR] [MODEL_PATH] [OUTPUT_PATH]
# Defaults:       ./data      ./pickle/model.pkl  ./output/predictions.csv
#
# One-shot: feature generation + prediction. No network, no prompts, no
# retraining (the committed pickle/model.pkl is pre-trained).

set -euo pipefail
cd "$(dirname "$0")"

DATA_DIR="${1:-./data}"
MODEL_PATH="${2:-./pickle/model.pkl}"
OUTPUT_PATH="${3:-./output/predictions.csv}"

OUTPUT_DIR="$(dirname "$OUTPUT_PATH")"
mkdir -p "$OUTPUT_DIR"
FEATURES_PATH="$OUTPUT_DIR/features.parquet"

echo "== AIgnition forecasting pipeline =="
echo "data:   $DATA_DIR"
echo "model:  $MODEL_PATH"
echo "output: $OUTPUT_PATH"

python -m src.generate_features --data-dir "$DATA_DIR" --out "$FEATURES_PATH"
python -m src.predict --features "$FEATURES_PATH" --model "$MODEL_PATH" --output "$OUTPUT_PATH"

echo "== done: $OUTPUT_PATH =="
echo ""
echo "Live dashboard -> https://presage-two.vercel.app/"
