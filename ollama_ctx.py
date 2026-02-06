#!/usr/bin/env python3
"""Standalone Ollama context injection utility.

Wraps Ollama's /api/chat endpoint with markdown file context injection.
Provides both a CLI tool and importable Python API.

Dependencies: requests + stdlib only.

CLI usage:
    python ollama_ctx.py -f README.md "What does this project do?"
    python ollama_ctx.py -f docs/api.md -f docs/auth.md "How do I authenticate?"
    cat CHANGELOG.md | python ollama_ctx.py --stdin "Summarize recent changes"

Python API:
    from ollama_ctx import OllamaContext
    ctx = OllamaContext(model="llama3.3:70b")
    answer = ctx.query("How does auth work?", context_files=["docs/auth.md"])
"""

import argparse
import os
import sys
import time
from typing import Optional

import requests

DEFAULT_MODEL = "llama3.3:70b-instruct-q3_K_M"
DEFAULT_HOST = "http://localhost:11434"
DEFAULT_NUM_CTX = 8192
DEFAULT_NUM_PREDICT = 4096
DEFAULT_TEMPERATURE = 0.3
DEFAULT_TIMEOUT = 300
DEFAULT_MAX_RETRIES = 3
MAX_NUM_CTX = 131072

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant. Answer questions using the provided "
    "documentation context."
)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using a conservative heuristic.

    Uses len(text) / 3.5 which tends to overestimate, which is safer
    for context window budgeting than underestimating.
    """
    return int(len(text) / 3.5)


def format_documents(file_paths: list[str], verbose: bool = False) -> tuple[str, int]:
    """Load files and wrap them in XML document tags.

    Args:
        file_paths: List of file paths to load.
        verbose: If True, print per-file token estimates to stderr.

    Returns:
        Tuple of (formatted document string, estimated token count).
    """
    documents = []
    total_tokens = 0

    for path in file_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Warning: file not found, skipping: {path}", file=sys.stderr)
            continue
        except UnicodeDecodeError:
            print(f"Warning: cannot decode file (not UTF-8), skipping: {path}", file=sys.stderr)
            continue

        tokens = estimate_tokens(content)
        total_tokens += tokens

        if verbose:
            print(f"  {path}: ~{tokens:,} tokens ({len(content):,} chars)", file=sys.stderr)

        documents.append(f'<document path="{path}">\n{content}\n</document>')

    formatted = "\n\n".join(documents)
    return formatted, total_tokens


class OllamaContext:
    """Core API for querying Ollama with document context injection."""

    def __init__(
        self,
        host: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        num_ctx: int = DEFAULT_NUM_CTX,
        temperature: float = DEFAULT_TEMPERATURE,
        num_predict: int = DEFAULT_NUM_PREDICT,
        top_p: float = 0.9,
        seed: Optional[int] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        verbose: bool = False,
    ):
        self.host = host or os.environ.get("OLLAMA_HOST", DEFAULT_HOST)
        self.model = model
        self.num_ctx = num_ctx
        self.temperature = temperature
        self.num_predict = num_predict
        self.top_p = top_p
        self.seed = seed
        self.timeout = timeout
        self.max_retries = max_retries
        self.verbose = verbose

    def query(
        self,
        question: str,
        context_files: Optional[list[str]] = None,
        system: Optional[str] = None,
    ) -> str:
        """Query Ollama with file-based context.

        Args:
            question: The question to ask.
            context_files: List of file paths to inject as context.
            system: Custom system prompt. Uses default if not provided.

        Returns:
            Model response text.
        """
        if context_files:
            context_text, context_tokens = format_documents(
                context_files, verbose=self.verbose
            )
        else:
            context_text, context_tokens = "", 0

        return self._send(question, context_text, context_tokens, system)

    def query_with_text(
        self,
        question: str,
        context_text: str,
        system: Optional[str] = None,
    ) -> str:
        """Query Ollama with pre-formatted text context.

        Args:
            question: The question to ask.
            context_text: Pre-formatted context string.
            system: Custom system prompt. Uses default if not provided.

        Returns:
            Model response text.
        """
        context_tokens = estimate_tokens(context_text)
        return self._send(question, context_text, context_tokens, system)

    def _send(
        self,
        question: str,
        context_text: str,
        context_tokens: int,
        system: Optional[str],
    ) -> str:
        """Build messages and send to Ollama."""
        system_prompt = system or DEFAULT_SYSTEM_PROMPT
        user_content = self._format_prompt(question, context_text)

        # Estimate total input tokens
        input_tokens = (
            estimate_tokens(system_prompt) + estimate_tokens(user_content)
        )

        # Auto-adjust num_ctx if input would overflow
        num_ctx = self.num_ctx
        required = input_tokens + self.num_predict
        if required > num_ctx:
            if required > MAX_NUM_CTX:
                raise ValueError(
                    f"Estimated input ({input_tokens:,} tokens) + output "
                    f"({self.num_predict:,} tokens) exceeds maximum context "
                    f"window ({MAX_NUM_CTX:,} tokens). Reduce context files "
                    f"or output length."
                )
            new_ctx = min(required + 512, MAX_NUM_CTX)  # 512 token buffer
            print(
                f"Warning: auto-adjusting num_ctx from {num_ctx:,} to "
                f"{new_ctx:,} (input ~{input_tokens:,} + output "
                f"{self.num_predict:,} tokens)",
                file=sys.stderr,
            )
            num_ctx = new_ctx

        if self.verbose:
            headroom = num_ctx - input_tokens - self.num_predict
            print(
                f"Context window: {num_ctx:,} tokens\n"
                f"  Input estimate: ~{input_tokens:,} tokens\n"
                f"  Output budget:  {self.num_predict:,} tokens\n"
                f"  Headroom:       ~{headroom:,} tokens",
                file=sys.stderr,
            )
            if context_tokens > 0 and context_tokens > num_ctx * 0.5:
                print(
                    f"  Warning: context is >{50}% of context window",
                    file=sys.stderr,
                )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        return self._request_with_retry(messages, num_ctx)

    def _format_prompt(self, question: str, context: str) -> str:
        """Format user message with context and question."""
        if not context:
            return question

        return (
            "I have provided reference documentation below. "
            "Use it to answer my question.\n\n"
            f"<context>\n{context}\n</context>\n\n"
            f"<question>\n{question}\n</question>"
        )

    def _request_with_retry(self, messages: list[dict], num_ctx: int) -> str:
        """Send request to Ollama with exponential backoff retry."""
        delay = 2.0
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": self.temperature,
                            "top_p": self.top_p,
                            "num_predict": self.num_predict,
                            "num_ctx": num_ctx,
                            **({"seed": self.seed} if self.seed is not None else {}),
                        },
                    },
                    timeout=self.timeout,
                )
                response.raise_for_status()
                return response.json()["message"]["content"]

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status = e.response.status_code if e.response is not None else None
                if status not in (503, 429):
                    raise
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ) as e:
                last_exception = e

            if attempt >= self.max_retries:
                raise RuntimeError(
                    f"Failed after {self.max_retries + 1} attempts: {last_exception}"
                ) from last_exception

            print(
                f"Attempt {attempt + 1}/{self.max_retries + 1} failed: "
                f"{last_exception}. Retrying in {delay:.0f}s...",
                file=sys.stderr,
            )
            time.sleep(delay)
            delay = min(delay * 2.0, 60.0)

        # Should not be reached
        raise RuntimeError(f"Unexpected retry exit: {last_exception}")


def main():
    parser = argparse.ArgumentParser(
        description="Query Ollama with document context injection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s -f README.md \"What does this project do?\"\n"
            "  %(prog)s -f docs/api.md -f docs/auth.md \"How do I authenticate?\"\n"
            "  cat CHANGELOG.md | %(prog)s --stdin \"Summarize recent changes\"\n"
            "  %(prog)s -m qwen2.5-coder:32b -s \"You are a code reviewer.\" "
            '-f src/main.py "Review this code"'
        ),
    )

    parser.add_argument("question", nargs="?", help="The question to ask")
    parser.add_argument(
        "-f", "--file", action="append", dest="files", metavar="FILE",
        help="Context file (repeatable)",
    )
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help=f"Ollama model (default: {DEFAULT_MODEL})",
    )
    parser.add_argument("-s", "--system", help="Custom system prompt")
    parser.add_argument(
        "--host",
        default=os.environ.get("OLLAMA_HOST", DEFAULT_HOST),
        help=f"Ollama host URL (default: $OLLAMA_HOST or {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--num-ctx", type=int, default=DEFAULT_NUM_CTX,
        help=f"Context window tokens (default: {DEFAULT_NUM_CTX})",
    )
    parser.add_argument(
        "--num-predict", type=int, default=DEFAULT_NUM_PREDICT,
        help=f"Max output tokens (default: {DEFAULT_NUM_PREDICT})",
    )
    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE})",
    )
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument(
        "--timeout", type=int, default=DEFAULT_TIMEOUT,
        help=f"Request timeout seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
        help=f"Max retries (default: {DEFAULT_MAX_RETRIES})",
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--stdin", action="store_true",
        help="Read context from stdin instead of files",
    )
    input_group.add_argument(
        "--question-stdin", action="store_true",
        help="Read question from stdin",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show token estimates and context window info",
    )

    args = parser.parse_args()

    # Validate: --stdin and -f are mutually exclusive
    if args.stdin and args.files:
        parser.error("--stdin and -f/--file are mutually exclusive")

    # Resolve question
    question = args.question
    if args.question_stdin:
        question = sys.stdin.read().strip()
    if not question:
        parser.error("a question is required (positional arg or --question-stdin)")

    ctx = OllamaContext(
        host=args.host,
        model=args.model,
        num_ctx=args.num_ctx,
        temperature=args.temperature,
        num_predict=args.num_predict,
        seed=args.seed,
        timeout=args.timeout,
        max_retries=args.max_retries,
        verbose=args.verbose,
    )

    if args.stdin:
        context_text = sys.stdin.read()
        if args.verbose:
            tokens = estimate_tokens(context_text)
            print(
                f"stdin context: ~{tokens:,} tokens ({len(context_text):,} chars)",
                file=sys.stderr,
            )
        answer = ctx.query_with_text(question, context_text, system=args.system)
    else:
        answer = ctx.query(
            question, context_files=args.files, system=args.system
        )

    print(answer)


if __name__ == "__main__":
    main()
