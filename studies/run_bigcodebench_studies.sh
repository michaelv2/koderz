#!/usr/bin/env bash
set -euo pipefail

# BigCodeBench-Hard Studies (148 tasks)
#
# Applies best configuration from HumanEval studies to BCB-Hard.
# BCB-Hard: 148 most challenging tasks, 30s timeout, unittest format.
#
# All studies use:
#   --dataset bigcodebench-hard
#   --temperature 0.0 --seed 23 (reproducibility)

COMMON="--start 0 --end 148 \
  --dataset bigcodebench-hard \
  --frontier-spec-model gpt-oss:20b \
  --frontier-checkpoint-model gpt-5-nano \
  --checkpoint-interval 5 \
  --temperature 0.0 --seed 23 \
  --debug --debug-dir ./debug"

echo "=============================================="
echo "BigCodeBench-Hard Studies (148 tasks)"
echo "=============================================="
echo ""

# BCB-1: Baseline — local model zero-shot
echo "[BCB-1] Baseline — gpt-oss:20b-128k × zero-shot, no-spec"
echo "  Purpose: Baseline local model capability on BCB-Hard"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --mode zero-shot \
  --no-spec
echo ""

# BCB-2: Frontier reference
echo "[BCB-2] Frontier reference — gpt-5-nano × zero-shot"
echo "  Purpose: Frontier reference point (matches HumanEval approach)"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-5-nano" \
  --mode zero-shot \
  --no-spec
echo ""

# BCB-3: Best config from Phase 3 (cascade + enhanced feedback + on-demand CP)
echo "[BCB-3] Optimized config — cascade + enhanced-feedback + on-demand CP"
echo "  Purpose: Apply optimized orchestration from HumanEval to BCB-Hard"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest" \
  --cascade-budget 2 \
  --enhanced-feedback \
  --checkpoint-strategy on-demand
echo ""

echo "=============================================="
echo "All BCB-Hard studies complete!"
echo "=============================================="
echo ""
echo "Run analysis:"
echo "  python studies/orchestration_improvements.py --include-live"
