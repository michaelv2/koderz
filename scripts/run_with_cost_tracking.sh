#!/usr/bin/env bash
#
# run_with_cost_tracking.sh — Wrap a Claude Code session with automatic cost tracking
#
# Captures the terminal session via `script`, then parses /cost output from the
# transcript. Type /cost before exiting to record cost/token data.
#
# Usage:
#   ./scripts/run_with_cost_tracking.sh [run-label] [claude-args...]
#
# Examples:
#   # Interactive session
#   ./scripts/run_with_cost_tracking.sh "run-b-orchestrated"
#
#   # With specific model
#   ./scripts/run_with_cost_tracking.sh "run-b-sonnet" --model sonnet
#
# Output:
#   results/<run-label>/transcript.log  — raw terminal capture
#   results/<run-label>/summary.json    — parsed cost/token summary
#
# Cost is captured automatically from the status bar. No special commands needed.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Parse arguments ---
RUN_LABEL="${1:-run-$(date +%Y%m%d-%H%M%S)}"
shift || true
CLAUDE_ARGS=("$@")

# --- Setup output directory ---
RESULTS_DIR="$PROJECT_DIR/results/$RUN_LABEL"
mkdir -p "$RESULTS_DIR"

TRANSCRIPT="$RESULTS_DIR/transcript.log"
SUMMARY_FILE="$RESULTS_DIR/summary.json"

echo "=== Cost-Tracked Claude Code Session ==="
echo "Run label:  $RUN_LABEL"
echo "Results:    $RESULTS_DIR/"
echo ""
echo "Cost is captured automatically from the status bar."
echo ""

# --- Record start time ---
START_TIME=$(date +%s)

# Unset the nesting guard so claude can launch
unset CLAUDECODE 2>/dev/null || true

# --- Run Claude Code under `script` to capture terminal output ---
set +e
if [ ${#CLAUDE_ARGS[@]} -eq 0 ]; then
    script -q -c "claude" "$TRANSCRIPT"
else
    script -q -c "claude ${CLAUDE_ARGS[*]}" "$TRANSCRIPT"
fi
CLAUDE_EXIT=$?
set -e

# --- Record end time ---
END_TIME=$(date +%s)
WALL_SECONDS=$((END_TIME - START_TIME))

echo ""
echo "--- Claude Code exited (code $CLAUDE_EXIT) ---"
echo ""

# --- Parse cost data from transcript ---
python3 - "$TRANSCRIPT" "$SUMMARY_FILE" "$WALL_SECONDS" "$RUN_LABEL" "$CLAUDE_EXIT" <<'PYEOF'
import json, re, sys

transcript_path, summary_path, wall_s, label, exit_code = sys.argv[1:6]

try:
    with open(transcript_path, "rb") as f:
        raw = f.read().decode("utf-8", errors="replace")
except FileNotFoundError:
    raw = ""

summary = {
    "run_label": label,
    "wall_clock_seconds": int(wall_s),
    "wall_clock_display": f"{int(wall_s) // 60}m {int(wall_s) % 60}s",
    "claude_exit_code": int(exit_code),
    "total_cost_usd": None,
    "api_duration": None,
    "wall_duration": None,
    "lines_added": None,
    "lines_removed": None,
}

# --- Strategy 1: Parse /cost command output (if user typed /cost) ---
# Strip ANSI for /cost command parsing
clean = re.sub(r'\x1b[\[\]()][^\x07\x1b]*[\x07a-zA-Z]|\x1b.', '', raw)
clean = clean.replace('\r', '')

cost_match = re.search(r'Total cost:\s*\$([0-9]+\.?[0-9]*)', clean)
if cost_match:
    summary["total_cost_usd"] = float(cost_match.group(1))
    summary["parse_method"] = "/cost_command"

api_dur = re.search(r'Total duration \(API\):\s*(.+?)(?:\n|$)', clean)
if api_dur:
    summary["api_duration"] = api_dur.group(1).strip()

wall_dur = re.search(r'Total duration \(wall\):\s*(.+?)(?:\n|$)', clean)
if wall_dur:
    summary["wall_duration"] = wall_dur.group(1).strip()

lines_match = re.search(r'(\d+)\s+lines?\s+added.*?(\d+)\s+lines?\s+removed', clean)
if lines_match:
    summary["lines_added"] = int(lines_match.group(1))
    summary["lines_removed"] = int(lines_match.group(2))

# --- Strategy 2: Parse status bar (always present in raw transcript) ---
# Status bar format: "Cost: $0.04" or "Cost: $2.13"
# Take the LAST occurrence (most up-to-date value at session end)
if summary["total_cost_usd"] is None:
    # Strip ANSI escapes from raw before status bar parsing
    raw_stripped = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw)
    # Try "Cost: $X.XX" or "Cost:$X.XX" (ANSI escapes between tokens now removed)
    statusbar_costs = re.findall(r'Cost:\s*\$([0-9]+\.[0-9]+)', raw_stripped)
    if not statusbar_costs:
        # Fallback: any "$X.XX" in the raw stream
        statusbar_costs = re.findall(r'\$([0-9]+\.[0-9]+)', raw_stripped)
    if statusbar_costs:
        summary["total_cost_usd"] = float(statusbar_costs[-1])
        summary["parse_method"] = "statusbar"

# --- Strategy 3: Parse context percentage from status bar ---
ctx_matches = re.findall(r'(\d+)%[│|]', raw)
if not ctx_matches:
    ctx_matches = re.findall(r'Ctx\s*\[.*?\]\s*(\d+)%', raw)
if ctx_matches:
    summary["context_percent"] = int(ctx_matches[-1])

with open(summary_path, "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))

if summary["total_cost_usd"] is None:
    print("\nWARNING: No cost data found in transcript.", file=sys.stderr)
PYEOF

echo ""
echo "=== Session Complete ==="
echo "Results:     $RESULTS_DIR/"
echo "  summary:   $SUMMARY_FILE"
echo "  transcript: $TRANSCRIPT"
