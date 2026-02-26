"""Multi-file extraction from model responses.

Extracts file paths and code from fenced code blocks in model output.
Shared by SWE-bench evaluation and orchestrate_subtask.py.
"""

import re


def _normalize_path(raw_path: str) -> str:
    """Strip leading 'path/to/' or similar placeholder prefixes from a file path."""
    cleaned = re.sub(r"^(?:path/to/)+", "", raw_path)
    return cleaned


def extract_files_from_response(content: str) -> list[dict]:
    """Extract file paths and code from fenced code blocks in a model response.

    Supports multiple detection strategies:

    1. Markdown heading before code block:
        ## path/to/file.py
        ```python
        ...code...
        ```

    2. Path comment as first line inside code block:
        ```python
        # path/to/file.py
        ...code...
        ```

    3. Path on line(s) immediately before the fence:
        # path/to/file.py
        ```python
        ...code...
        ```

    Also handles "File:" prefix and "path/to/" placeholder prefixes.

    Args:
        content: Raw model response text

    Returns:
        List of {"path": "relative/file.py", "code": "..."} dicts.
        Blocks without a recognized path are skipped.
    """
    PATH_RE = r"^#\s*(?:File:\s*)?(\S+\.(?:py|js|ts|jsx|tsx|java|go|rs|rb|c|cpp|h|hpp|cs|yml|yaml|toml|cfg|ini|txt|md|json|xml|html|css|sh|sql))\s*$"
    HEADING_RE = r"^##\s+(?:File:\s*)?`?(\S+\.(?:py|js|ts|jsx|tsx|java|go|rs|rb|c|cpp|h|hpp|cs|yml|yaml|toml|cfg|ini|txt|md|json|xml|html|css|sh|sql))`?\s*$"

    files = []
    content_lines = content.split("\n")
    i = 0

    while i < len(content_lines):
        line = content_lines[i]

        # Check if this line opens a code fence
        if re.match(r"^```(?:python|diff|javascript|typescript|java|go|rust|ruby|c|cpp|csharp|bash|sh|sql|yaml|toml|json|xml|html|css)?\s*$", line.strip()):
            fence_start = i
            # Collect block contents until closing fence
            block_lines = []
            i += 1
            while i < len(content_lines) and not content_lines[i].strip().startswith("```"):
                block_lines.append(content_lines[i])
                i += 1
            i += 1  # skip closing ```

            if not block_lines:
                continue

            path = None

            # Strategy 1: path on first line inside the block (# comment)
            first_line = block_lines[0].strip()
            path_match = re.match(PATH_RE, first_line)
            if path_match:
                path = _normalize_path(path_match.group(1))
                code = "\n".join(block_lines[1:]).strip() + "\n"
            else:
                code = "\n".join(block_lines).strip() + "\n"

            # Strategy 2: heading or path comment on line(s) before the fence
            if not path:
                for j in range(fence_start - 1, max(fence_start - 4, -1), -1):
                    if j < 0:
                        break
                    prev = content_lines[j].strip()
                    if not prev:
                        continue
                    # Try ## heading format
                    heading_match = re.match(HEADING_RE, prev)
                    if heading_match:
                        path = _normalize_path(heading_match.group(1))
                        break
                    # Try # comment format
                    prev_match = re.match(PATH_RE, prev)
                    if prev_match:
                        path = _normalize_path(prev_match.group(1))
                        break
                    break  # Stop at first non-empty, non-matching line

            if path:
                files.append({"path": path, "code": code})
        else:
            i += 1

    return files
