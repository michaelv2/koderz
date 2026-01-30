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
        self.frontier_costs.append({
            "cost": cost,
            "model": model,
            "operation": operation
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

        return {
            "actual_cost": actual_cost,
            "frontier_cost": self.total_frontier_cost(),
            "local_cost": self.total_local_cost(),
            "frontier_only_cost": frontier_only_cost,
            "savings": savings,
            "savings_pct": savings_pct,
            "iterations": iterations,
            "frontier_calls": len(self.frontier_costs),
            "local_calls": len(self.local_costs)
        }

    def format_analysis(self, iterations: int) -> str:
        """Format cost analysis as readable text.

        Args:
            iterations: Number of iterations performed

        Returns:
            Formatted analysis string
        """
        analysis = self.calculate_savings(iterations)

        return f"""Cost Analysis:
  Actual Total: ${analysis['actual_cost']:.4f}
    - Frontier: ${analysis['frontier_cost']:.4f} ({analysis['frontier_calls']} calls)
    - Local: ${analysis['local_cost']:.4f} ({analysis['local_calls']} calls)

  Frontier-Only Estimate: ${analysis['frontier_only_cost']:.4f}
  Savings: ${analysis['savings']:.4f} ({analysis['savings_pct']:.1f}%)

  Total Iterations: {analysis['iterations']}
"""
