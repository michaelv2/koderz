#!/bin/bash
# notify-on-complete.sh
# Wrapper script that runs a command and sends a Slack notification when it completes.
#
# Usage:
#   ./notify-on-complete.sh <command> [args...]
#
# Example:
#   ./notify-on-complete.sh koderz benchmark --start 0 --end 50 --local-model qwen2.5-coder:7b
#
# Configuration:
#   Set SLACK_WEBHOOK_URL environment variable or in .env file

set -euo pipefail

# Load .env file if it exists
if [ -f "$(dirname "$0")/.env" ]; then
    set -a
    source "$(dirname "$0")/.env"
    set +a
fi

# Check for webhook URL
if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "Error: SLACK_WEBHOOK_URL not set" >&2
    echo "Set it in .env file or as environment variable" >&2
    exit 1
fi

# Check for command
if [ $# -eq 0 ]; then
    echo "Usage: $0 <command> [args...]" >&2
    exit 1
fi

# Record start time and command
START_TIME=$(date +%s)
START_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMAND="$*"
HOSTNAME=$(hostname)

echo "Starting: $COMMAND"
echo "Start time: $START_TIMESTAMP"
echo "Slack notifications enabled to: ${SLACK_WEBHOOK_URL:0:30}..."
echo ""

# Run the command, capture output and exit code
OUTPUT_FILE=$(mktemp)
set +e
"$@" 2>&1 | tee "$OUTPUT_FILE"
EXIT_CODE=$?
set -e

# Calculate duration
END_TIME=$(date +%s)
END_TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))
DURATION_SEC=$((DURATION % 60))

# Get last few lines of output for context
TAIL_OUTPUT=$(tail -n 5 "$OUTPUT_FILE" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Build Slack message
if [ $EXIT_CODE -eq 0 ]; then
    STATUS="✅ SUCCESS"
    COLOR="good"
else
    STATUS="❌ FAILED (exit code: $EXIT_CODE)"
    COLOR="danger"
fi

# Escape command for JSON
COMMAND_ESCAPED=$(echo "$COMMAND" | sed 's/"/\\"/g')

MESSAGE=$(cat <<EOF
{
  "attachments": [{
    "color": "$COLOR",
    "title": "$STATUS: Command completed",
    "text": "\`$COMMAND_ESCAPED\`",
    "fields": [
      {
        "title": "Duration",
        "value": "${DURATION_MIN}m ${DURATION_SEC}s",
        "short": true
      },
      {
        "title": "Host",
        "value": "$HOSTNAME",
        "short": true
      },
      {
        "title": "Started",
        "value": "$START_TIMESTAMP",
        "short": true
      },
      {
        "title": "Completed",
        "value": "$END_TIMESTAMP",
        "short": true
      }
    ],
    "footer": "Last 5 lines of output"
  }]
}
EOF
)

# Add output preview if available
if [ -n "$TAIL_OUTPUT" ]; then
    MESSAGE=$(echo "$MESSAGE" | sed 's/}]}/},{"text":"```\n'"$TAIL_OUTPUT"'\n```","color":"'"$COLOR"'"}]}/')
fi

# Send to Slack
echo ""
echo "Sending Slack notification..."
CURL_OUTPUT=$(mktemp)
HTTP_CODE=$(curl -s -w "%{http_code}" -X POST \
    -H 'Content-type: application/json' \
    --data "$MESSAGE" \
    "$SLACK_WEBHOOK_URL" \
    -o "$CURL_OUTPUT")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✓ Slack notification sent successfully"
else
    echo "✗ Slack notification failed (HTTP $HTTP_CODE)" >&2
    cat "$CURL_OUTPUT" >&2
fi

# Clean up
rm -f "$OUTPUT_FILE" "$CURL_OUTPUT"

# Exit with original command's exit code
exit $EXIT_CODE
