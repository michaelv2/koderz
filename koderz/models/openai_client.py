"""OpenAI model client."""

from openai import OpenAI
from typing import Optional

from .registry import calculate_cost


class OpenAIClient:
    """Client for calling OpenAI models via OpenAI API."""

    def __init__(self, api_key: str):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.total_cost = 0.0

    def generate_spec(self, problem: str, model: str = "gpt-4o-mini") -> dict:
        """Generate detailed implementation spec for a problem.

        Args:
            problem: Problem description or code prompt
            model: Model to use for generation

        Returns:
            Dictionary with 'spec' (str) and 'cost' (float)
        """
        prompt = f"""Generate a MINIMAL implementation specification for the following coding problem:

{problem}

Your spec should include ONLY:
1. Problem analysis - What is the core challenge? What are the constraints?
2. Implementation specification - What should the function do? What should it return?

CRITICAL - Do NOT include:
- Implementation approach or algorithm suggestions
- Edge cases or common pitfalls
- Test criteria or examples
- Reference implementation, pseudocode, or code skeleton
- Specific data structures or algorithms to use

Keep the spec minimal. The goal is to clarify WHAT needs to be done, not HOW to do it.
This spec will guide a coding model that should solve the problem independently."""

        response = self.client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        cost, usage = self._calculate_cost(response.usage, model)
        self.total_cost += cost

        return {
            "spec": response.choices[0].message.content,
            "cost": cost,
            "usage": usage
        }

    def checkpoint_review(
        self,
        iterations: list[dict],
        model: str = "gpt-4o-mini",
        checkpoint_num: int = 1,
        problem_prompt: Optional[str] = None
    ) -> dict:
        """Review recent iterations and provide guidance.

        Args:
            iterations: List of recent iteration memories with code and results
            model: Model to use for review
            checkpoint_num: Which checkpoint this is (1, 2, 3, etc.)
            problem_prompt: Original problem prompt for progressive spec generation

        Returns:
            Dictionary with 'review' (str), 'guidance' (str), and 'cost' (float)
        """
        def format_iteration(i, iter_data):
            metadata = iter_data.get('metadata', {})
            success = metadata.get('success', False)
            iter_num = iter_data.get('iteration', i+1)

            # Get test metrics
            tests_passed = metadata.get('tests_passed', 0)
            tests_total = metadata.get('tests_total', 0)
            test_pass_rate = metadata.get('test_pass_rate', 0.0)

            text = f"### Iteration {iter_num}\n**Code:**\n```python\n{iter_data['content']}\n```\n"

            if success:
                text += f"**Result:** ✓ PASSED all {tests_total} tests (100%)"
            else:
                error = metadata.get('error', 'Unknown error')
                stderr = metadata.get('stderr', '')

                # Show test metrics prominently
                text += f"**Result:** ✗ FAILED - {tests_passed}/{tests_total} tests passed ({test_pass_rate:.1%})\n"
                text += f"**Error:** {error}"
                if stderr and stderr != error:
                    text += f"\n**Stderr:** {stderr}"

            return text, test_pass_rate

        # Format iterations and track test pass rates for plateau detection
        formatted_iterations = []
        pass_rates = []
        for i, iter_data in enumerate(iterations):
            formatted, rate = format_iteration(i, iter_data)
            formatted_iterations.append(formatted)
            pass_rates.append(rate)

        iterations_text = "\n\n".join(formatted_iterations)

        # Detect plateau (same pass rate for 3+ consecutive iterations)
        plateau_detected = False
        plateau_info = ""
        if len(pass_rates) >= 3:
            # Check if last 3 rates are the same and not 0.0 or 1.0
            last_three = pass_rates[-3:]
            if len(set(last_three)) == 1 and 0.0 < last_three[0] < 1.0:
                plateau_detected = True
                plateau_info = f"\n\n⚠️ PLATEAU DETECTED: Model stuck at {last_three[0]:.1%} pass rate for {len([r for r in pass_rates if r == last_three[0]])} consecutive iterations."

        # Build structured prompt with 4 required sections
        prompt = f"""You are an expert code reviewer providing guidance to a local coding model that is attempting to solve a programming problem.

{iterations_text}{plateau_info}

You must provide a SYSTEMATIC ANALYSIS following this exact structure:

## 1. FAILING TEST ANALYSIS
Identify the specific test case(s) that are failing:
- What is the current test pass rate and what does it tell us?
- Based on the error message, what specific input is causing the failure?
- What output does the code produce vs. what is expected?
- If this is an AssertionError, analyze the traceback to determine which assertion failed

## 2. ROOT CAUSE DIAGNOSIS
Trace through the code execution step-by-step with the failing input:
- Walk through each line of code with the failing input
- Show what values variables have at each critical step
- Identify the exact line or operator where the behavior diverges from expected
- Explain WHY this line causes the failure (wrong operator, missing condition, off-by-one, etc.)

## 3. PROPOSED FIX
Provide specific, actionable code changes:
- Show the exact line(s) that need to change
- Provide the corrected code
- Explain WHY this fix addresses the root cause
- If this is a plateau (stuck at same pass rate), suggest a CREATIVE alternative approach

## 4. EDGE CASES TO VERIFY
List other test cases that might fail with similar logic:
- What edge cases should be verified after this fix?
- Are there boundary conditions that need special handling?

IMPORTANT:
- Be SPECIFIC, not generic. Don't say "fix the logic" - show the exact code change.
- If stuck at a plateau, the current approach may be fundamentally wrong - suggest rethinking the algorithm.
- Use the test pass rate to gauge how close the solution is (0% = completely wrong, 70%+ = almost there).

Provide your analysis in the exact 4-section format above."""

        # Generate progressive spec disclosure based on checkpoint number
        progressive_spec = ""
        if checkpoint_num == 1 and problem_prompt:
            # Checkpoint 1: Implementation approach, edge cases, common pitfalls
            spec_prompt = f"""Based on the failing code attempts above for this problem:

{problem_prompt}

Provide STRATEGIC GUIDANCE (not tactical debugging) to help the model understand:

## Implementation Approach
What high-level algorithm or strategy should be used? (e.g., "sorting enables O(n log n)", "use a hash map for O(1) lookup")
Consider what the failed attempts reveal about the model's understanding.

## Edge Cases to Handle
What special scenarios must be handled? (empty input, single element, duplicates, boundary values, etc.)
Focus on edge cases that seem to be causing failures based on the error patterns.

## Common Pitfalls
What mistakes should be avoided? (off-by-one errors, wrong operators, performance issues, etc.)
Highlight pitfalls evident in the failed attempts.

Keep this concise and actionable - this is strategic guidance, not a solution."""

            progressive_spec = "\n\n---\n\n**STRATEGIC GUIDANCE FROM SENIOR DEVELOPER:**\n\n"

        elif checkpoint_num == 2 and problem_prompt:
            # Checkpoint 2: Test criteria
            spec_prompt = f"""Based on the failing code attempts above for this problem:

{problem_prompt}

Provide TEST-FOCUSED GUIDANCE to help the model understand what correctness means:

## Test Criteria & Expected Behavior
What are specific test cases that should pass? Include:
- Normal cases with expected outputs
- Edge cases with expected behavior
- Corner cases the model might miss

Focus on tests that would catch the types of errors seen in the failed attempts.

Keep this concise - show representative test cases, not exhaustive coverage."""

            progressive_spec = "\n\n---\n\n**TEST CRITERIA FROM SENIOR DEVELOPER:**\n\n"

        else:
            # Checkpoint 3+: No additional spec sections, just debugging guidance
            spec_prompt = None

        # Generate combined response
        if spec_prompt:
            # Combine debugging analysis + progressive spec in single call
            combined_prompt = f"""{prompt}

---

After providing your 4-section analysis above, also generate this additional section:

{spec_prompt}"""

            response = self.client.chat.completions.create(
                model=model,
                max_tokens=4096,  # Increased for combined output
                messages=[{
                    "role": "user",
                    "content": combined_prompt
                }]
            )
        else:
            # Just debugging analysis (checkpoint 3+)
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=3072,  # Standard size for debugging only
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

        cost, usage = self._calculate_cost(response.usage, model)
        self.total_cost += cost

        text = response.choices[0].message.content

        # The entire response is the guidance (already structured)
        # Extract just the actionable parts for "guidance" field if possible
        # Otherwise use full text as both
        if "## 3. PROPOSED FIX" in text:
            # Extract from section 3 onwards as the actionable guidance
            parts = text.split("## 3. PROPOSED FIX", 1)
            review = parts[0].strip()
            guidance = "## 3. PROPOSED FIX" + parts[1].strip()
        else:
            # Fallback: use full text
            review = text
            guidance = text

        return {
            "review": review,
            "guidance": guidance,
            "cost": cost,
            "usage": usage
        }

    def _calculate_cost(self, usage, model: str) -> tuple[float, dict]:
        """Calculate API cost from token usage.

        Args:
            usage: Usage object from API response
            model: Model name used

        Returns:
            Tuple of (cost in USD, usage dict with token counts)
        """
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # OpenAI reports cached tokens inside prompt_tokens_details
        details = getattr(usage, 'prompt_tokens_details', None)
        cache_read_tokens = getattr(details, 'cached_tokens', 0) or 0

        cost = calculate_cost(
            model, input_tokens, output_tokens,
            cache_read_tokens=cache_read_tokens,
        )

        usage_dict = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_tokens": cache_read_tokens,
            "cache_creation_tokens": 0,
        }

        return cost, usage_dict

    def get_total_cost(self) -> float:
        """Get total accumulated cost.

        Returns:
            Total cost in USD
        """
        return self.total_cost
