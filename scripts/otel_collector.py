#!/usr/bin/env python3
"""
Lightweight OTLP HTTP/JSON collector that writes telemetry to a JSONL file.

Accepts POST requests on /v1/metrics, /v1/logs, and /v1/traces,
writing each payload as a JSON line to the output file.

Usage:
    python otel_collector.py [--port 4318] [--output telemetry.jsonl]
"""

import argparse
import json
import signal
import sys
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer


class OTLPHandler(BaseHTTPRequestHandler):
    output_file = None
    _lock = threading.Lock()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Binary protobuf — acknowledge but skip (we need JSON)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{}')
            return

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": self.path,
            "payload": payload,
        }

        with self._lock:
            with open(self.output_file, "a") as f:
                f.write(json.dumps(record) + "\n")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{}')

    def log_message(self, format, *args):
        pass  # suppress request logs


def summarize(output_file: str) -> dict:
    """Parse the JSONL telemetry file and summarize costs/tokens."""
    total_cost = 0.0
    total_input = 0
    total_output = 0
    total_cache_read = 0
    total_cache_creation = 0
    api_calls = 0
    models_used = set()

    try:
        with open(output_file) as f:
            for line in f:
                record = json.loads(line)
                payload = record.get("payload", {})
                path = record.get("path", "")

                # Primary cost/token data comes from api_request log events below.
                # /v1/metrics contains cumulative counters which are harder to
                # deduplicate, so we only use them to discover model names.
                if "/v1/metrics" in path:
                    _collect_model_names(payload, models_used)

                # Parse log events (api_request events have per-call detail)
                if "/v1/logs" in path:
                    for resource_log in payload.get("resourceLogs", []):
                        for scope_log in resource_log.get("scopeLogs", []):
                            for log_record in scope_log.get("logRecords", []):
                                attrs = _attrs_to_dict(
                                    log_record.get("attributes", [])
                                )
                                event_name = attrs.get(
                                    "event.name",
                                    log_record.get("body", {}).get(
                                        "stringValue", ""
                                    ),
                                )
                                if "api_request" in str(event_name):
                                    api_calls += 1
                                    cost = _to_float(attrs.get("cost_usd", 0))
                                    total_cost += cost
                                    total_input += _to_int(
                                        attrs.get("input_tokens", 0)
                                    )
                                    total_output += _to_int(
                                        attrs.get("output_tokens", 0)
                                    )
                                    total_cache_read += _to_int(
                                        attrs.get("cache_read_tokens", 0)
                                    )
                                    total_cache_creation += _to_int(
                                        attrs.get("cache_creation_tokens", 0)
                                    )
                                    model = attrs.get("model", "unknown")
                                    if model != "unknown":
                                        models_used.add(model)
    except FileNotFoundError:
        pass

    return {
        "total_cost_usd": round(total_cost, 4),
        "api_calls": api_calls,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cache_read_tokens": total_cache_read,
        "total_cache_creation_tokens": total_cache_creation,
        "models_used": sorted(models_used),
    }


def _attrs_to_dict(attrs: list) -> dict:
    """Convert OTLP attribute list to a flat dict."""
    result = {}
    for attr in attrs:
        key = attr.get("key", "")
        value = attr.get("value", {})
        if "stringValue" in value:
            result[key] = value["stringValue"]
        elif "intValue" in value:
            result[key] = value["intValue"]
        elif "doubleValue" in value:
            result[key] = value["doubleValue"]
        elif "boolValue" in value:
            result[key] = value["boolValue"]
    return result


def _to_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _to_int(v) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _collect_model_names(payload, models_used):
    """Extract model names from OTLP metrics payload attributes."""
    for resource_metric in payload.get("resourceMetrics", []):
        for scope_metric in resource_metric.get("scopeMetrics", []):
            for metric in scope_metric.get("metrics", []):
                data_points = (
                    metric.get("sum", {}).get("dataPoints", [])
                    or metric.get("gauge", {}).get("dataPoints", [])
                    or metric.get("histogram", {}).get("dataPoints", [])
                )
                for dp in data_points:
                    attrs = _attrs_to_dict(dp.get("attributes", []))
                    model = attrs.get("model", "")
                    if model:
                        models_used.add(model)


def main():
    parser = argparse.ArgumentParser(description="Lightweight OTLP file collector")
    parser.add_argument("--port", type=int, default=4318)
    parser.add_argument("--output", default="telemetry.jsonl")
    parser.add_argument(
        "--summarize", action="store_true",
        help="Summarize an existing telemetry file instead of running the server",
    )
    args = parser.parse_args()

    if args.summarize:
        summary = summarize(args.output)
        print(json.dumps(summary, indent=2))
        return

    OTLPHandler.output_file = args.output

    # Clear output file
    with open(args.output, "w") as f:
        pass

    server = HTTPServer(("127.0.0.1", args.port), OTLPHandler)
    print(f"OTLP collector listening on http://127.0.0.1:{args.port}", file=sys.stderr)
    print(f"Writing telemetry to {args.output}", file=sys.stderr)

    # Run server in a daemon thread so signal handlers can shut it down
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    stop = threading.Event()

    def shutdown(sig, frame):
        print("\nCollector shutting down...", file=sys.stderr)
        stop.set()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    stop.wait()
    server.shutdown()
    server.server_close()

    summary = summarize(args.output)
    print("\n=== Telemetry Summary ===", file=sys.stderr)
    print(json.dumps(summary, indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
