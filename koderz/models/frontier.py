"""Anthropic frontier model client."""

from anthropic import Anthropic
from typing import Optional


class FrontierClient:
    """Client for calling frontier models via Anthropic API."""

    # Pricing per 1M tokens (as of Jan 2025)
    PRICING = {
        "claude-opus-4-5": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-sonnet-4": {"input": 3.0, "output": 15.0},
    }

    def __init__(self, api_key: str):
        """Initialize frontier client.

        Args:
            api_key: Anthropic API key
        """
        self.client = Anthropic(api_key=api_key)
        self.total_cost = 0.0

    def generate_spec(self, problem: str, model: str = "claude-opus-4-5") -> dict:
        """Generate detailed implementation spec for a problem.

        Args:
            problem: Problem description or code prompt
            model: Model to use for generation

        Returns:
            Dictionary with 'spec' (str) and 'cost' (float)
        """
        prompt = f"""Generate a detailed implementation specification for the following coding problem:

{problem}

Your spec should include:
1. Problem analysis - What is the core challenge?
2. Implementation approach - High-level strategy
3. Test criteria - What makes a solution correct?
4. Edge cases - Special scenarios to handle
5. Common pitfalls - What mistakes to avoid

Be specific and actionable. This spec will guide a coding model."""

        response = self.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        cost = self._calculate_cost(response.usage, model)
        self.total_cost += cost

        return {
            "spec": response.content[0].text,
            "cost": cost
        }

    def checkpoint_review(self, iterations: list[dict], model: str = "claude-sonnet-4-5") -> dict:
        """Review recent iterations and provide guidance.

        Args:
            iterations: List of recent iteration memories with code and results
            model: Model to use for review

        Returns:
            Dictionary with 'review' (str), 'guidance' (str), and 'cost' (float)
        """
        iterations_text = "\n\n".join([
            f"### Iteration {i+1}\n**Code:**\n```python\n{iter['content']}\n```\n**Result:** {iter.get('metadata', {}).get('success', 'Unknown')}"
            for i, iter in enumerate(iterations)
        ])

        prompt = f"""Review these recent coding attempts by a local model:

{iterations_text}

Analyze:
1. What patterns of errors do you see?
2. What is the model missing or misunderstanding?
3. What specific guidance would help it succeed?

Provide concrete, actionable advice for the next iteration."""

        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        cost = self._calculate_cost(response.usage, model)
        self.total_cost += cost

        text = response.content[0].text

        # Split into review and guidance sections if possible
        parts = text.split("Guidance:", 1) if "Guidance:" in text else [text, ""]

        return {
            "review": parts[0].strip(),
            "guidance": parts[1].strip() if len(parts) > 1 else parts[0].strip(),
            "cost": cost
        }

    def _calculate_cost(self, usage, model: str) -> float:
        """Calculate API cost from token usage.

        Args:
            usage: Usage object from API response
            model: Model name used

        Returns:
            Cost in USD
        """
        pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (usage.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (usage.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def get_total_cost(self) -> float:
        """Get total accumulated cost.

        Returns:
            Total cost in USD
        """
        return self.total_cost
