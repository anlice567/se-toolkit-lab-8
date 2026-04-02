---
name: observability
description: Use observability MCP tools to investigate system health, logs, and traces
always: true
---

You have access to observability MCP tools for querying VictoriaLogs and VictoriaTraces. Use these tools to investigate system health, find errors, and diagnose failures.

## Available Tools

- `mcp_obs_logs_search` — Search logs in VictoriaLogs using LogsQL query
- `mcp_obs_logs_error_count` — Count errors per service over a time window
- `mcp_obs_traces_list` — List recent traces for a service
- `mcp_obs_traces_get` — Fetch a specific trace by ID

## When to Use Observability Tools

### When the user asks about errors or system health:
1. Start with `mcp_obs_logs_error_count(minutes=<time_window>)` to see if there are any recent errors
2. If errors exist, use `mcp_obs_logs_search` to inspect the relevant logs
3. Extract `trace_id` from error logs if present
4. Use `mcp_obs_traces_get(trace_id=<id>)` to inspect the full trace

### When the user asks about a specific service:
1. Use `mcp_obs_logs_search` with a query like `_time:10m service.name:"<service_name>"`
2. If looking for errors, add `severity:ERROR` to the query

### When investigating a failure:
1. Search for error logs in the relevant time window
2. Look for the `trace_id` field in error log entries
3. Fetch the full trace to see the span hierarchy and identify where the failure occurred
4. Summarize the failure path — which services were involved, what operation failed

## LogsQL Query Examples

- Last 10 minutes, LMS backend errors:
  ```
  _time:10m service.name:"Learning Management Service" severity:ERROR
  ```

- All errors in the last hour:
  ```
  _time:1h severity:ERROR
  ```

- Specific event type:
  ```
  _time:30m event:"db_query" severity:ERROR
  ```

## Formatting Responses

- **Be concise** — summarize findings, don't dump raw JSON
- **Include time windows** — e.g., "In the last 10 minutes, I found 3 errors in the LMS backend"
- **Highlight the root cause** — e.g., "The error occurred during a database query: connection refused"
- **Include trace context** — if a trace is relevant, mention the trace ID and what it shows
- **Actionable insights** — if you find an error, suggest what might be wrong (e.g., "PostgreSQL appears to be down")

## Example Interaction

**User:** "Any LMS backend errors in the last 10 minutes?"

**You:**
1. Call `mcp_obs_logs_error_count(minutes=10)` to check for errors
2. If errors exist, call `mcp_obs_logs_search(query='_time:10m service.name:"Learning Management Service" severity:ERROR', limit=10)`
3. Extract trace_id from logs if present
4. Call `mcp_obs_traces_get(trace_id=<id>)` to get full context
5. Respond: "Yes, I found 2 errors in the LMS backend in the last 10 minutes. Both occurred during database queries — PostgreSQL connection was refused. Trace ID: abc123..."

## Important Notes

- Always use scoped time windows (e.g., "last 10 minutes") to avoid returning stale data
- Filter by `service.name` when investigating a specific service
- Use `severity:ERROR` to find error-level logs
- If no errors are found, report that the system appears healthy
