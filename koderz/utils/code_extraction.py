"""Code extraction utilities for isolating executable Python code from model responses."""

import re
import ast
from typing import Optional


def extract_code(response: str) -> str:
    """Extract code from markdown fenced code blocks or plain text.

    This function tries multiple strategies to extract clean Python code:
    1. Python-specific markdown code blocks (```python)
    2. Generic markdown code blocks (```)
    3. Extract first code block if multiple exist
    4. Return as-is if no markdown detected

    Args:
        response: Raw model response text

    Returns:
        Extracted Python code
    """
    # Strategy 1: Try Python code block first
    python_pattern = r"```python\n(.*?)\n```"
    match = re.search(python_pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Strategy 2: Try generic code block
    generic_pattern = r"```\n(.*?)\n```"
    match = re.search(generic_pattern, response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Strategy 3: Try without newlines after opening
    python_pattern_alt = r"```python(.*?)```"
    match = re.search(python_pattern_alt, response, re.DOTALL)
    if match:
        return match.group(1).strip()

    generic_pattern_alt = r"```(.*?)```"
    match = re.search(generic_pattern_alt, response, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Strategy 4: If no markdown, try to extract lines that look like code
    # Look for lines starting with 'def ', 'class ', 'import ', 'from '
    lines = response.split('\n')
    code_lines = []
    in_code = False

    for line in lines:
        stripped = line.strip()
        # Start collecting when we see code-like patterns
        if stripped.startswith(('def ', 'class ', 'import ', 'from ', 'async def ')):
            in_code = True

        if in_code:
            code_lines.append(line)

    if code_lines:
        return '\n'.join(code_lines).strip()

    # Strategy 5: Return as-is if nothing else works
    return response.strip()


def extract_function_name(code: str) -> Optional[str]:
    """Extract the first function name defined in the code.

    Args:
        code: Python code string

    Returns:
        Function name or None if not found
    """
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
    except SyntaxError:
        pass

    # Fallback to regex
    match = re.search(r"def\s+(\w+)\s*\(", code)
    if match:
        return match.group(1)

    return None


def ensure_prompt_imports(code: str, prompt: str) -> str:
    """Prepend import lines from the problem prompt if missing from the code.

    Models often emit just the function body and drop the ``from typing import ...``
    or ``import math`` lines that appear in the HumanEval prompt.  This function
    extracts ALL import statements from the prompt (including those inside function
    bodies, e.g. HumanEval/115) and prepends any that are not already present
    in *code*.

    Args:
        code: Extracted solution code from model output.
        prompt: Original HumanEval problem prompt.

    Returns:
        Code with missing imports prepended (unchanged if nothing was missing).
    """
    # Collect all import lines from anywhere in the prompt
    import_lines = []
    for line in prompt.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            if stripped not in import_lines:
                import_lines.append(stripped)

    if not import_lines:
        return code

    # Only prepend lines not already present
    missing = [line for line in import_lines if line not in code]
    if not missing:
        return code

    return "\n".join(missing) + "\n\n" + code


def validate_python_syntax(code: str) -> tuple[bool, Optional[str]]:
    """Validate that code is syntactically correct Python.

    Args:
        code: Python code string

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)
