"""Model speed benchmarking utility."""

import time
import logging
import requests
from typing import Optional
from dataclasses import dataclass

from ..utils.retry import retry_with_backoff, MaxRetriesExceeded

logger = logging.getLogger(__name__)


@dataclass
class PromptResult:
    """Result from a single prompt test."""
    prompt_name: str
    model: str
    tokens_generated: int
    eval_duration_ns: int
    prompt_eval_duration_ns: int
    total_duration_ns: int
    tokens_per_sec: float
    total_time_sec: float


@dataclass
class ModelSpeedResult:
    """Aggregated results for a model."""
    model: str
    prompt_results: list[PromptResult]
    avg_tokens_per_sec: float
    total_time_sec: float


# Warmup prompt - quick task to load model into memory
WARMUP_PROMPT = {
    "name": "Warmup",
    "prompt": "Write a haiku about computers.",
    "system": "You are a helpful assistant."
}

# Standard test prompts
STANDARD_PROMPTS = {
    "essay": {
        "name": "Historical Essay (200 words)",
        "prompt": "Write a 200-word essay about the fall of the Roman Empire, focusing on the key economic and political factors that contributed to its decline.",
        "system": "You are a knowledgeable historian. Provide a concise, well-structured response."
    },
    "coding": {
        "name": "Coding Problem",
        "prompt": """Write a Python function that takes a list of integers and returns the two numbers that sum to a target value.

Example:
Input: [2, 7, 11, 15], target = 9
Output: [2, 7]

Include error handling for edge cases.""",
        "system": "You are an expert Python programmer. Write clean, efficient code with comments."
    },
    "brain_teaser": {
        "name": "Brain Teaser",
        "prompt": "Three people check into a hotel room that costs $30. They each contribute $10. Later, the manager realizes the room should only cost $25 and gives the bellhop $5 to return. The bellhop keeps $2 and gives each person $1 back. Now each person has paid $9 (totaling $27) and the bellhop has $2, which equals $29. Where did the missing dollar go? Explain the logical error in this puzzle.",
        "system": "You are a logical thinker. Explain your reasoning clearly and concisely."
    }
}


class ModelSpeedBenchmark:
    """Benchmark local model inference speed."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        timeout: int = 300,
        max_retries: int = 3
    ):
        """Initialize speed benchmark.

        Args:
            host: Ollama host URL
            timeout: Request timeout in seconds (default: 300)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        self.host = host
        self.timeout = timeout
        self.max_retries = max_retries

    def test_model(self, model: str, prompts: Optional[dict] = None, warmup: bool = True) -> ModelSpeedResult:
        """Test a model with standard prompts.

        Args:
            model: Model name to test
            prompts: Optional custom prompts dict (defaults to STANDARD_PROMPTS)
            warmup: If True, run a warmup prompt first to load model into memory

        Returns:
            ModelSpeedResult with performance metrics
        """
        if prompts is None:
            prompts = STANDARD_PROMPTS

        # Warmup: load model into memory with a quick task
        if warmup:
            self._warmup_model(model)

        prompt_results = []

        for prompt_key, prompt_data in prompts.items():
            result = self._test_single_prompt(
                model=model,
                prompt_name=prompt_data["name"],
                prompt=prompt_data["prompt"],
                system=prompt_data.get("system")
            )
            prompt_results.append(result)

        # Calculate aggregated metrics
        avg_tokens_per_sec = sum(r.tokens_per_sec for r in prompt_results) / len(prompt_results)
        total_time_sec = sum(r.total_time_sec for r in prompt_results)

        return ModelSpeedResult(
            model=model,
            prompt_results=prompt_results,
            avg_tokens_per_sec=avg_tokens_per_sec,
            total_time_sec=total_time_sec
        )

    def _warmup_model(self, model: str) -> None:
        """Warmup model by running a quick prompt to load it into memory.

        Args:
            model: Model name to warm up
        """
        messages = []
        if WARMUP_PROMPT.get("system"):
            messages.append({"role": "system", "content": WARMUP_PROMPT["system"]})
        messages.append({"role": "user", "content": WARMUP_PROMPT["prompt"]})

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100  # Short response for warmup
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()
        except Exception as e:
            # Warmup failure is not critical, log and continue anyway
            logger.warning(f"Warmup failed for {model}: {e}")
            pass

    def _test_single_prompt(
        self,
        model: str,
        prompt_name: str,
        prompt: str,
        system: Optional[str] = None
    ) -> PromptResult:
        """Test a single prompt and measure performance with automatic retry.

        Args:
            model: Model name
            prompt_name: Name/description of the prompt
            prompt: The prompt text
            system: Optional system prompt

        Returns:
            PromptResult with timing metrics

        Raises:
            MaxRetriesExceeded: When all retry attempts are exhausted
        """
        @retry_with_backoff(
            max_retries=self.max_retries,
            initial_delay=2.0,
            backoff_factor=2.0,
            max_delay=60.0
        )
        def _make_request():
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            wall_start = time.time()

            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 2048
                    }
                },
                timeout=self.timeout
            )
            response.raise_for_status()

            wall_end = time.time()
            wall_time_sec = wall_end - wall_start

            data = response.json()

            # Extract timing metrics from ollama response
            # These are in nanoseconds
            eval_count = data.get("eval_count", 0)  # tokens generated
            eval_duration = data.get("eval_duration", 0)  # time to generate
            prompt_eval_duration = data.get("prompt_eval_duration", 0)  # time to process prompt
            total_duration = data.get("total_duration", 0)  # total time

            # Calculate tokens per second
            # Use eval_duration (generation time) for pure generation speed
            if eval_duration > 0 and eval_count > 0:
                tokens_per_sec = (eval_count / eval_duration) * 1e9  # convert ns to seconds
            else:
                tokens_per_sec = 0.0

            return PromptResult(
                prompt_name=prompt_name,
                model=model,
                tokens_generated=eval_count,
                eval_duration_ns=eval_duration,
                prompt_eval_duration_ns=prompt_eval_duration,
                total_duration_ns=total_duration,
                tokens_per_sec=tokens_per_sec,
                total_time_sec=wall_time_sec
            )

        return _make_request()

    def benchmark_models(self, models: list[str], warmup: bool = True) -> list[ModelSpeedResult]:
        """Benchmark multiple models with automatic retry on failure.

        Args:
            models: List of model names to test
            warmup: If True, warmup each model before testing

        Returns:
            List of ModelSpeedResult, one per model (excludes failed models)
        """
        results = []
        failed_models = []

        for model in models:
            if warmup:
                print(f"Testing {model} (with warmup, max {self.max_retries} retries)...")
            else:
                print(f"Testing {model} (max {self.max_retries} retries)...")

            try:
                result = self.test_model(model, warmup=warmup)
                results.append(result)
                print(f"  ✓ Completed successfully")

            except MaxRetriesExceeded as e:
                error_msg = f"Max retries exceeded: {e}"
                print(f"  ✗ Failed: {error_msg}")
                failed_models.append((model, error_msg))
                continue

            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ Failed: {error_msg}")
                failed_models.append((model, error_msg))
                continue

        # Report summary of failures if any
        if failed_models:
            print(f"\n⚠ {len(failed_models)} model(s) failed:")
            for model, error in failed_models:
                print(f"  • {model}: {error}")

        return results

    @staticmethod
    def print_results(results: list[ModelSpeedResult]) -> None:
        """Print results in a formatted table.

        Args:
            results: List of ModelSpeedResult to display
        """
        if not results:
            print("No results to display.")
            return

        print("\n" + "="*120)
        print("MODEL SPEED BENCHMARK RESULTS")
        print("="*120)

        # Overall summary table
        print("\nOVERALL SUMMARY")
        print("-"*120)
        print(f"{'Model':<30} | {'Avg Tokens/sec':<15} | {'Total Time (s)':<15} | {'Relative Speed':<15}")
        print("-"*120)

        # Calculate relative speeds (compared to slowest)
        if results:
            slowest_speed = min(r.avg_tokens_per_sec for r in results)

            for result in sorted(results, key=lambda r: r.avg_tokens_per_sec, reverse=True):
                relative_speed = result.avg_tokens_per_sec / slowest_speed if slowest_speed > 0 else 0
                print(
                    f"{result.model:<30} | "
                    f"{result.avg_tokens_per_sec:>14.2f} | "
                    f"{result.total_time_sec:>14.2f} | "
                    f"{relative_speed:>14.2f}x"
                )

        # Detailed per-prompt breakdown
        print("\n" + "="*120)
        print("DETAILED BREAKDOWN BY PROMPT")
        print("="*120)

        for result in results:
            print(f"\n{result.model}")
            print("-"*120)
            print(f"{'Prompt':<35} | {'Tokens':<10} | {'Tokens/sec':<15} | {'Time (s)':<12}")
            print("-"*120)

            for pr in result.prompt_results:
                print(
                    f"{pr.prompt_name:<35} | "
                    f"{pr.tokens_generated:>9} | "
                    f"{pr.tokens_per_sec:>14.2f} | "
                    f"{pr.total_time_sec:>11.2f}"
                )

        print("\n" + "="*120)

    @staticmethod
    def export_json(results: list[ModelSpeedResult], output_file: str) -> None:
        """Export results to JSON file.

        Args:
            results: List of ModelSpeedResult to export
            output_file: Path to output JSON file
        """
        import json
        from pathlib import Path

        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "models": []
        }

        for result in results:
            model_data = {
                "model": result.model,
                "avg_tokens_per_sec": result.avg_tokens_per_sec,
                "total_time_sec": result.total_time_sec,
                "prompts": [
                    {
                        "name": pr.prompt_name,
                        "tokens_generated": pr.tokens_generated,
                        "tokens_per_sec": pr.tokens_per_sec,
                        "total_time_sec": pr.total_time_sec,
                        "eval_duration_ns": pr.eval_duration_ns,
                        "prompt_eval_duration_ns": pr.prompt_eval_duration_ns,
                        "total_duration_ns": pr.total_duration_ns
                    }
                    for pr in result.prompt_results
                ]
            }
            data["models"].append(model_data)

        Path(output_file).write_text(json.dumps(data, indent=2))
        print(f"\nResults exported to: {output_file}")
