"""Frontier cost registry for accurate baseline comparisons.

Records actual costs from frontier model runs per problem, enabling
accurate cost comparisons when evaluating local models.

IMPORTANT: Baseline costs assume zero-shot mode with --no-spec for fair
comparison to standard benchmark conditions. When comparing against a
baseline, ensure you're running with similar settings or the comparison
may not be meaningful.
"""

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Optional


DEFAULT_REGISTRY_PATH = Path("benchmark_results/frontier_costs.json")


class FrontierCostRegistry:
    """Registry for storing and querying frontier model costs per problem."""

    def __init__(self, path: Optional[Path] = None):
        """Initialize the registry.

        Args:
            path: Path to the registry JSON file. Defaults to
                  benchmark_results/frontier_costs.json
        """
        self.path = path or DEFAULT_REGISTRY_PATH
        self._data = self._load()

    def _load(self) -> dict:
        """Load registry from disk."""
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save(self):
        """Save registry to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))

    def record(
        self,
        model: str,
        problem_id: str,
        cost: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        dataset: str = "humaneval",
        temperature: float = 0.1,
        seed: Optional[int] = None,
        success: bool = True,
    ):
        """Record a frontier model cost for a problem.

        Args:
            model: Model name (e.g., "gpt-5-mini")
            problem_id: Problem ID (e.g., "HumanEval/0")
            cost: Actual cost in USD
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_read_tokens: Number of cache read tokens
            cache_creation_tokens: Number of cache creation tokens
            dataset: Dataset used ("humaneval" or "humaneval+")
            temperature: Temperature setting used
            seed: Random seed if set
            success: Whether the problem was solved successfully
        """
        if model not in self._data:
            self._data[model] = {}

        if problem_id not in self._data[model]:
            self._data[model][problem_id] = {
                "runs": [],
                "median_cost": 0.0,
                "run_count": 0,
            }

        entry = self._data[model][problem_id]

        # Append new run
        run = {
            "cost": cost,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
            },
            "timestamp": datetime.now().isoformat(),
            "config": {
                "dataset": dataset,
                "temperature": temperature,
                "seed": seed,
            },
            "success": success,
        }

        # Include cache tokens only if present
        if cache_read_tokens or cache_creation_tokens:
            run["tokens"]["cache_read"] = cache_read_tokens
            run["tokens"]["cache_creation"] = cache_creation_tokens

        entry["runs"].append(run)
        entry["run_count"] = len(entry["runs"])

        # Recalculate median from successful runs only
        successful_costs = [r["cost"] for r in entry["runs"] if r.get("success", True)]
        if successful_costs:
            entry["median_cost"] = statistics.median(successful_costs)
        else:
            # Fall back to all runs if none successful
            entry["median_cost"] = statistics.median([r["cost"] for r in entry["runs"]])

        self._save()

    def get_cost(
        self,
        model: str,
        problem_id: str,
        dataset: Optional[str] = None,
    ) -> Optional[float]:
        """Get the median cost for a model/problem pair.

        Args:
            model: Model name
            problem_id: Problem ID
            dataset: Optional filter by dataset

        Returns:
            Median cost in USD, or None if not found
        """
        if model not in self._data:
            return None
        if problem_id not in self._data[model]:
            return None

        entry = self._data[model][problem_id]

        # If dataset filter specified, recalculate from matching runs
        if dataset:
            matching_costs = [
                r["cost"]
                for r in entry["runs"]
                if r.get("config", {}).get("dataset") == dataset
                and r.get("success", True)
            ]
            if matching_costs:
                return statistics.median(matching_costs)
            return None

        return entry.get("median_cost")

    def get_total_cost(
        self,
        model: str,
        problem_ids: list[str],
        dataset: Optional[str] = None,
    ) -> tuple[float, int, int]:
        """Get total cost for a list of problems.

        Args:
            model: Model name
            problem_ids: List of problem IDs
            dataset: Optional filter by dataset

        Returns:
            Tuple of (total_cost, found_count, missing_count)
        """
        total = 0.0
        found = 0
        missing = 0

        for pid in problem_ids:
            cost = self.get_cost(model, pid, dataset=dataset)
            if cost is not None:
                total += cost
                found += 1
            else:
                missing += 1

        return total, found, missing

    def get_run_details(
        self,
        model: str,
        problem_id: str,
    ) -> Optional[dict]:
        """Get full run details for a model/problem pair.

        Args:
            model: Model name
            problem_id: Problem ID

        Returns:
            Dict with runs, median_cost, run_count, or None if not found
        """
        if model not in self._data:
            return None
        return self._data[model].get(problem_id)

    def list_models(self) -> list[str]:
        """List all models in the registry."""
        return list(self._data.keys())

    def list_problems(self, model: str) -> list[str]:
        """List all problems recorded for a model."""
        if model not in self._data:
            return []
        return list(self._data[model].keys())

    def get_model_summary(self, model: str, dataset: Optional[str] = None) -> dict:
        """Get summary statistics for a model.

        Args:
            model: Model name
            dataset: Optional filter by dataset

        Returns:
            Dict with problem_count, total_median_cost, avg_cost_per_problem
        """
        if model not in self._data:
            return {"problem_count": 0, "total_median_cost": 0.0, "avg_cost_per_problem": 0.0}

        problems = self._data[model]
        costs = []

        for pid, entry in problems.items():
            cost = self.get_cost(model, pid, dataset=dataset)
            if cost is not None:
                costs.append(cost)

        if not costs:
            return {"problem_count": 0, "total_median_cost": 0.0, "avg_cost_per_problem": 0.0}

        return {
            "problem_count": len(costs),
            "total_median_cost": sum(costs),
            "avg_cost_per_problem": sum(costs) / len(costs),
        }

    def prune_old_runs(self, older_than_days: int, dry_run: bool = True) -> dict:
        """Remove runs older than specified days.

        Args:
            older_than_days: Remove runs older than this many days
            dry_run: If True, only report what would be removed

        Returns:
            Dict with counts of removed runs per model
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=older_than_days)
        removed = {}

        for model in self._data:
            removed[model] = 0
            for problem_id in self._data[model]:
                entry = self._data[model][problem_id]
                original_count = len(entry["runs"])

                if not dry_run:
                    entry["runs"] = [
                        r for r in entry["runs"]
                        if datetime.fromisoformat(r["timestamp"]) >= cutoff
                    ]
                    entry["run_count"] = len(entry["runs"])

                    # Recalculate median
                    if entry["runs"]:
                        successful_costs = [
                            r["cost"] for r in entry["runs"]
                            if r.get("success", True)
                        ]
                        if successful_costs:
                            entry["median_cost"] = statistics.median(successful_costs)
                        else:
                            entry["median_cost"] = statistics.median(
                                [r["cost"] for r in entry["runs"]]
                            )
                    else:
                        entry["median_cost"] = 0.0

                    removed[model] += original_count - len(entry["runs"])
                else:
                    # Dry run: count what would be removed
                    would_remove = sum(
                        1 for r in entry["runs"]
                        if datetime.fromisoformat(r["timestamp"]) < cutoff
                    )
                    removed[model] += would_remove

        if not dry_run:
            self._save()

        return removed
