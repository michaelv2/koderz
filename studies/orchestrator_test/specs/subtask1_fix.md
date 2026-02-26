# Fix: DuckDB interval parameter binding

Four methods fail because DuckDB does not support `?` parameter placeholders inside `INTERVAL` expressions.

The fix: use Python f-string to interpolate the integer value directly into the SQL for the interval part (these are always integers from function arguments, not user input, so this is safe). Keep `?` for string parameters like domain.

## Methods to fix in `agentmon/storage/db.py`:

1. **`mark_domain_blocked`**: Change `interval ? second` to `interval '{max_age_seconds} seconds'` using an f-string. Keep the `?` for the domain parameter.

2. **`cleanup_old_data`**: Change `interval ? day` to `interval '{dns_days} days'` and `interval '{alerts_days} days'` using f-strings.

3. **`get_client_stats`**: Change `interval ? hour` to `interval '{hours} hours'` using an f-string.

Remember to put `# agentmon/storage/db.py` as the first line in the code block.
Output the COMPLETE file, not just the changed methods.
