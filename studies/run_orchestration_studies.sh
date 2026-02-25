#!/usr/bin/env bash
set -euo pipefail

# Orchestration Improvement Studies — HumanEval (164 problems)
#
# Control: bench_9d5ae700_20260213_092628.json
#   gpt-oss:20b-128k × 10 iter, gpt-5-nano CP, checkpoint_interval=5
#   Result: 161/164 (98.2%), $0.012
#
# All studies use:
#   --temperature 0.0 --seed 23 (reproducibility)
#   --frontier-checkpoint-model gpt-5-nano
#   --checkpoint-interval 5
#   --debug --debug-dir ./debug

COMMON="--start 0 --end 164 \
  --frontier-spec-model gpt-oss:20b \
  --frontier-checkpoint-model gpt-5-nano \
  --checkpoint-interval 5 \
  --temperature 0.0 --seed 23 \
  --debug --debug-dir ./debug"

echo "=============================================="
echo "Orchestration Improvement Studies — HumanEval"
echo "=============================================="
echo ""

# Study 3: Enhanced Feedback
echo "[Study 3] Enhanced Feedback — gpt-oss:20b-128k × 10 iter + enhanced-feedback"
echo "  Testing: Does structured feedback improve iter-2 self-recovery rate?"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --max-iterations 10 \
  --enhanced-feedback
echo ""

# Study 4: On-Demand Checkpoints
echo "[Study 4] On-Demand Checkpoints — gpt-oss:20b-128k × 10 iter + on-demand CP"
echo "  Testing: Same score at lower checkpoint cost?"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --max-iterations 10 \
  --checkpoint-strategy on-demand
echo ""

# Study 5: Model-Aware Specs (using qwen3-coder which is sensitive to spec wording)
echo "[Study 5] Model-Aware Specs — qwen3-coder:latest × 5 iter + model-aware-specs"
echo "  Testing: Fewer qwen3 regressions with tailored specs?"
poetry run koderz benchmark $COMMON \
  --local-model "qwen3-coder:latest" \
  --max-iterations 5 \
  --model-aware-specs
echo ""

# Study 6a: Cascade
echo "[Study 6a] Model Cascade — gpt-oss→nemotron→qwen3, 2 iter each"
echo "  Testing: Same score with fewer total iterations?"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest" \
  --cascade-budget 2
echo ""

# Study 6b: Combined (best of all improvements)
echo "[Study 6b] Combined — cascade + enhanced-feedback + on-demand CP"
echo "  Testing: Best overall config?"
poetry run koderz benchmark $COMMON \
  --local-model "gpt-oss:20b-128k" \
  --cascade-models "gpt-oss:20b-128k,nemotron-3-nano:30b,qwen3-coder:latest" \
  --cascade-budget 2 \
  --enhanced-feedback \
  --checkpoint-strategy on-demand
echo ""

echo "=============================================="
echo "All studies complete!"
echo "=============================================="
echo ""
echo "Run analysis:"
echo "  python studies/orchestration_improvements.py --include-live"
