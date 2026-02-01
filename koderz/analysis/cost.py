"""Cost analysis utilities for experiments."""

from typing import Optional


class CostAnalyzer:
    """Analyze experiment costs and compute savings."""

    def __init__(self):
        """Initialize cost analyzer."""
        self.frontier_costs = []
        self.local_costs = []

    def add_frontier_cost(self, cost: float, model: str, operation: str):
        """Record a frontier model cost.

        Args:
            cost: Cost in USD
            model: Model name
            operation: Operation type (spec/checkpoint/review)
        """
        from ..models.registry import get_tier
        self.frontier_costs.append({
            "cost": cost,
            "model": model,
            "operation": operation,
            "tier": get_tier(model)
        })

    def add_local_cost(self, cost: float, model: str, operation: str):
        """Record a local model cost.

        Args:
            cost: Cost in USD (typically 0 for local)
            model: Model name
            operation: Operation type (iteration)
        """
        self.local_costs.append({
            "cost": cost,
            "model": model,
            "operation": operation
        })

    def total_frontier_cost(self) -> float:
        """Calculate total frontier model costs.

        Returns:
            Total cost in USD
        """
        return sum(c["cost"] for c in self.frontier_costs)

    def total_local_cost(self) -> float:
        """Calculate total local model costs.

        Returns:
            Total cost in USD
        """
        return sum(c["cost"] for c in self.local_costs)

    def total_cost(self) -> float:
        """Calculate total experiment cost.

        Returns:
            Total cost in USD
        """
        return self.total_frontier_cost() + self.total_local_cost()

    def total_cost_by_tier(self) -> dict:
        """Calculate total cost per tier.

        Returns:
            Dictionary with cost per tier
        """
        tiers = {"local": 0.0, "small_frontier": 0.0, "frontier": 0.0}
        for cost_entry in self.frontier_costs:
            tier = cost_entry.get("tier", "frontier")
            tiers[tier] += cost_entry["cost"]
        # Local is always 0
        return tiers

    def estimate_frontier_only_cost(
        self,
        iterations: int,
        avg_frontier_cost: Optional[float] = None
    ) -> float:
        """Estimate cost if frontier model did all iterations.

        Args:
            iterations: Number of iterations performed
            avg_frontier_cost: Average cost per frontier call (auto-calculated if None)

        Returns:
            Estimated cost in USD
        """
        if avg_frontier_cost is None:
            if not self.frontier_costs:
                # Default assumption: ~$0.05 per iteration with Opus
                avg_frontier_cost = 0.05
            else:
                avg_frontier_cost = self.total_frontier_cost() / len(self.frontier_costs)

        return iterations * avg_frontier_cost

    def calculate_savings(self, iterations: int) -> dict:
        """Calculate cost savings vs frontier-only approach.

        Args:
            iterations: Number of iterations performed

        Returns:
            Dictionary with cost breakdown and savings
        """
        actual_cost = self.total_cost()
        frontier_only_cost = self.estimate_frontier_only_cost(iterations)

        savings = frontier_only_cost - actual_cost
        savings_pct = (savings / frontier_only_cost * 100) if frontier_only_cost > 0 else 0

        # Breakdown by tier
        by_tier = self.total_cost_by_tier()

        return {
            "actual_cost": actual_cost,
            "frontier_cost": self.total_frontier_cost(),
            "local_cost": self.total_local_cost(),
            "frontier_only_cost": frontier_only_cost,
            "savings": savings,
            "savings_pct": savings_pct,
            "breakdown": by_tier,
            "iterations": iterations,
            "frontier_calls": len(self.frontier_costs),
            "local_calls": len(self.local_costs)
        }

    def get_costs_by_operation(self) -> dict:
        """Group costs by operation type with model info.

        Returns:
            Dictionary mapping operation -> list of cost entries
        """
        ops = {}

        # Group frontier costs
        for entry in self.frontier_costs:
            op = entry['operation']
            if op not in ops:
                ops[op] = {'frontier': [], 'local': []}
            ops[op]['frontier'].append(entry)

        # Group local costs
        for entry in self.local_costs:
            op = entry['operation']
            if op not in ops:
                ops[op] = {'frontier': [], 'local': []}
            ops[op]['local'].append(entry)

        return ops

    def format_analysis(self, iterations: int) -> str:
        """Format cost analysis as readable text.

        Args:
            iterations: Number of iterations performed

        Returns:
            Formatted analysis string
        """
        analysis = self.calculate_savings(iterations)
        breakdown = analysis['breakdown']
        by_operation = self.get_costs_by_operation()

        # Build detailed breakdown by phase
        details = []

        # Spec phase
        if 'spec' in by_operation:
            spec_entries = by_operation['spec']
            if spec_entries['frontier']:
                for entry in spec_entries['frontier']:
                    details.append(f"  Spec ({entry['model']}): ${entry['cost']:.4f}")
            if spec_entries['local']:
                for entry in spec_entries['local']:
                    details.append(f"  Spec ({entry['model']}): $0.0000 (local)")

        # Iteration phase
        if 'iteration' in by_operation:
            iter_entries = by_operation['iteration']
            frontier_iter_cost = sum(e['cost'] for e in iter_entries['frontier'])
            local_iter_count = len(iter_entries['local'])

            if iter_entries['frontier']:
                # Group by model
                frontier_models = {}
                for entry in iter_entries['frontier']:
                    model = entry['model']
                    if model not in frontier_models:
                        frontier_models[model] = {'count': 0, 'cost': 0.0}
                    frontier_models[model]['count'] += 1
                    frontier_models[model]['cost'] += entry['cost']

                for model, info in frontier_models.items():
                    details.append(f"  Iterations ({model}): ${info['cost']:.4f} ({info['count']} calls)")

            if iter_entries['local']:
                # Group by model
                local_models = {}
                for entry in iter_entries['local']:
                    model = entry['model']
                    local_models[model] = local_models.get(model, 0) + 1

                for model, count in local_models.items():
                    details.append(f"  Iterations ({model}): $0.0000 ({count} local calls)")

        # Checkpoint phase
        if 'checkpoint' in by_operation:
            ckpt_entries = by_operation['checkpoint']
            if ckpt_entries['frontier']:
                for entry in ckpt_entries['frontier']:
                    details.append(f"  Checkpoint ({entry['model']}): ${entry['cost']:.4f}")
            if ckpt_entries['local']:
                for entry in ckpt_entries['local']:
                    details.append(f"  Checkpoint ({entry['model']}): $0.0000 (local)")

        details_str = "\n".join(details) if details else "  No costs recorded"

        return f"""Cost Analysis:
{details_str}
  ─────────────────────────────────────
  Total: ${analysis['actual_cost']:.4f}

  Tier Breakdown:
    - Full Frontier: ${breakdown['frontier']:.4f}
    - Small Frontier: ${breakdown['small_frontier']:.4f}
    - Local: ${breakdown['local']:.4f}

  Savings vs Frontier-Only:
    - Frontier-Only Estimate: ${analysis['frontier_only_cost']:.4f}
    - Actual Cost: ${analysis['actual_cost']:.4f}
    - Savings: ${analysis['savings']:.4f} ({analysis['savings_pct']:.1f}%)
"""
