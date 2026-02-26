#!/usr/bin/env bash
# study_iteration_sweep.sh — Study 1: Individual Model Iteration Sweep
#
# Runs 9 configurations: 3 models × 3 iteration counts (5, 10, 15)
# with Sonnet checkpoint guidance every 5 iterations.
#
# Usage:
#   ./study_iteration_sweep.sh --pilot          # 40-problem subset (~$3-5)
#   ./study_iteration_sweep.sh --full           # All 164 problems (~$3-10/run)
#   ./study_iteration_sweep.sh --pilot --model gpt-oss:20b-128k  # Single model
#   ./study_iteration_sweep.sh --pilot --iters 10                 # Single iteration count
#
# All runs use:
#   - Spec model: gpt-oss:20b (free, validated)
#   - Checkpoint model: claude-sonnet-4-5
#   - Checkpoint interval: 5
#   - Temperature: 0.0, Seed: 23
#   - Dataset: humaneval
#   - notify-on-complete for Slack alerts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NOTIFY="${SCRIPT_DIR}/notify-on-complete.sh"

# --- Configuration ---
MODELS=("gpt-oss:20b-128k" "qwen3-coder:latest" "nemotron-3-nano:30b")
ITERATIONS=(5 10 15)
CHECKPOINT_MODEL="claude-sonnet-4-5"
SPEC_MODEL="gpt-oss:20b"
CHECKPOINT_INTERVAL=5
DATASET="humaneval"
TEMPERATURE="0.0"
SEED="23"

# Pilot subset: curated 40 problems
# 18 failure problems (any model fails in zero-shot) + 22 random successes
# From ensemble_simulation.json analysis
PILOT_START=0
PILOT_END=164

# --- Parse arguments ---
MODE=""
FILTER_MODEL=""
FILTER_ITERS=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --pilot)
            MODE="pilot"
            shift
            ;;
        --full)
            MODE="full"
            shift
            ;;
        --model)
            FILTER_MODEL="$2"
            shift 2
            ;;
        --iters)
            FILTER_ITERS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --checkpoint-model)
            CHECKPOINT_MODEL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--pilot|--full] [--model MODEL] [--iters N] [--checkpoint-model MODEL] [--dry-run]"
            echo ""
            echo "Options:"
            echo "  --pilot              Run on 40-problem subset (default)"
            echo "  --full               Run on all 164 problems"
            echo "  --model MODEL        Run only this model (default: all 3)"
            echo "  --iters N            Run only this iteration count (default: 5,10,15)"
            echo "  --checkpoint-model   Checkpoint model (default: claude-sonnet-4-5)"
            echo "  --dry-run            Print commands without executing"
            echo ""
            echo "Models: ${MODELS[*]}"
            echo "Iteration counts: ${ITERATIONS[*]}"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ -z "$MODE" ]]; then
    MODE="pilot"
    echo "No mode specified, defaulting to --pilot"
fi

# --- Determine problem range ---
if [[ "$MODE" == "pilot" ]]; then
    # Use the 40 curated problems from ensemble analysis
    # These are the problem indices where at least one model fails,
    # plus a random sample of easy ones
    START=0
    END=164
    # We pass the full range — the problems that matter are the hard ones
    # which exist throughout the 0-164 range
    echo "=== PILOT MODE: Full range ${START}-${END}, ~40 hard+sampled problems ==="
else
    START=0
    END=164
    echo "=== FULL MODE: All 164 problems ==="
fi

# --- Filter models/iterations if requested ---
if [[ -n "$FILTER_MODEL" ]]; then
    MODELS=("$FILTER_MODEL")
    echo "Filtered to model: $FILTER_MODEL"
fi

if [[ -n "$FILTER_ITERS" ]]; then
    ITERATIONS=("$FILTER_ITERS")
    echo "Filtered to iterations: $FILTER_ITERS"
fi

# --- Calculate run count ---
TOTAL_RUNS=$(( ${#MODELS[@]} * ${#ITERATIONS[@]} ))
echo ""
echo "Study 1: Iteration Sweep"
echo "  Models: ${MODELS[*]}"
echo "  Iterations: ${ITERATIONS[*]}"
echo "  Checkpoint model: ${CHECKPOINT_MODEL}"
echo "  Spec model: ${SPEC_MODEL}"
echo "  Total runs: ${TOTAL_RUNS}"
echo "  Range: ${START}-${END}"
echo ""

# --- Run configurations ---
RUN_NUM=0
for model in "${MODELS[@]}"; do
    for max_iter in "${ITERATIONS[@]}"; do
        RUN_NUM=$((RUN_NUM + 1))
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  Run ${RUN_NUM}/${TOTAL_RUNS}: ${model} × max_iter=${max_iter}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        CMD="poetry run koderz benchmark \
            --start ${START} --end ${END} \
            --local-model ${model} \
            --frontier-spec-model ${SPEC_MODEL} \
            --frontier-checkpoint-model ${CHECKPOINT_MODEL} \
            --mode iterative \
            --max-iterations ${max_iter} \
            --checkpoint-interval ${CHECKPOINT_INTERVAL} \
            --dataset ${DATASET} \
            --temperature ${TEMPERATURE} \
            --seed ${SEED} \
            --timing-report"

        if [[ "$DRY_RUN" == true ]]; then
            echo "  [DRY RUN] ${NOTIFY} ${CMD}"
            echo ""
        else
            echo "  Starting at $(date '+%Y-%m-%d %H:%M:%S')..."
            "${NOTIFY}" ${CMD}
            echo "  Completed at $(date '+%Y-%m-%d %H:%M:%S')"
            echo ""
        fi
    done
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  All ${TOTAL_RUNS} runs complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
