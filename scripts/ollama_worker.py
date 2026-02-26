#!/usr/bin/env python3
"""
Ollama worker — sends coding prompts to local models and returns responses.

Usage:
    # Interactive (reads prompt from stdin)
    echo "Write a hello world function" | python scripts/ollama_worker.py

    # From file
    python scripts/ollama_worker.py --prompt-file subtask_spec.md

    # With specific model and host
    python scripts/ollama_worker.py --model gpt-oss:20b-128k --host http://192.168.1.74:11434

    # Extract code blocks only
    python scripts/ollama_worker.py --extract-code --prompt-file spec.md

    # Save raw response and extracted code
    python scripts/ollama_worker.py --prompt-file spec.md --output-raw resp.txt --output-code code.py
"""

import argparse
import json
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import URLError


HOSTS = {
    "gpu-server": "http://192.168.1.74:11434",
    "local": "http://192.168.1.180:11434",
}

DEFAULT_HOST = HOSTS["gpu-server"]
DEFAULT_MODEL = "gpt-oss:20b-128k"


def call_ollama(
    prompt: str,
    model: str = DEFAULT_MODEL,
    host: str = DEFAULT_HOST,
    system: str = "",
    temperature: float = 0.2,
    num_ctx: int = 32768,
    timeout: int = 300,
) -> dict:
    """Send a chat request to Ollama and return the response."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,
        },
    }).encode()

    req = Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    start = time.time()
    resp = urlopen(req, timeout=timeout)
    data = json.loads(resp.read())
    elapsed = time.time() - start

    content = data.get("message", {}).get("content", "")
    eval_count = data.get("eval_count", 0)
    prompt_eval_count = data.get("prompt_eval_count", 0)

    return {
        "content": content,
        "model": model,
        "host": host,
        "elapsed_seconds": round(elapsed, 1),
        "prompt_tokens": prompt_eval_count,
        "completion_tokens": eval_count,
    }


def extract_code_blocks(text: str) -> str:
    """Extract Python code from markdown fenced blocks."""
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        return "\n\n".join(blocks)
    # If no fenced blocks, return the whole thing (might be plain code)
    return text


def main():
    parser = argparse.ArgumentParser(description="Ollama coding worker")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--system", default="You are an expert Python developer. Write clean, correct code. Always wrap code in ```python fenced blocks.")
    parser.add_argument("--prompt-file", help="Read prompt from file instead of stdin")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--num-ctx", type=int, default=32768)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--extract-code", action="store_true", help="Output only extracted code blocks")
    parser.add_argument("--output-raw", help="Save raw response to file")
    parser.add_argument("--output-code", help="Save extracted code to file")
    parser.add_argument("--json", action="store_true", help="Output full JSON response")
    args = parser.parse_args()

    if args.prompt_file:
        with open(args.prompt_file) as f:
            prompt = f.read()
    else:
        prompt = sys.stdin.read()

    if not prompt.strip():
        print("Error: empty prompt", file=sys.stderr)
        sys.exit(1)

    print(f"Calling {args.model} on {args.host}...", file=sys.stderr)

    try:
        result = call_ollama(
            prompt=prompt,
            model=args.model,
            host=args.host,
            system=args.system,
            temperature=args.temperature,
            num_ctx=args.num_ctx,
            timeout=args.timeout,
        )
    except URLError as e:
        print(f"Error connecting to {args.host}: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Done in {result['elapsed_seconds']}s "
        f"({result['prompt_tokens']} prompt + {result['completion_tokens']} completion tokens)",
        file=sys.stderr,
    )

    if args.output_raw:
        with open(args.output_raw, "w") as f:
            f.write(result["content"])

    code = extract_code_blocks(result["content"])
    if args.output_code:
        with open(args.output_code, "w") as f:
            f.write(code)

    if args.json:
        print(json.dumps(result, indent=2))
    elif args.extract_code:
        print(code)
    else:
        print(result["content"])


if __name__ == "__main__":
    main()
