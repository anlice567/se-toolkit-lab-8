---
name: observability
description: Use observability MCP tools to investigate system health, logs, and traces
always: true
---

You have access to observability MCP tools for querying VictoriaLogs and VictoriaTraces. Use these tools to investigate system health, find errors, and diagnose failures.

## Available Tools

The tools are registered with the `mcp_` prefix. Use these exact names:

- `mcp_mcp_obs_logs_search` — Search logs in VictoriaLogs using LogsQL query
- `mcp_mcp_obs_logs_error_count` — Count errors per service over a time window
- `mcp_mcp_obs_traces_list` — List recent traces for a service
- `mcp_mcp_obs_traces_get` — Fetch a specific trace by ID

## When to Use Observability Tools

### When the user asks "What went wrong?" or "Check system health":
**ALWAYS** follow this investigation flow:
1. **First**, call `mcp_mcp_obs_logs_error_count(minutes=10)` to see if there are any recent errors
2. **If errors exist**, call `mcp_mcp_obs_logs_search(query='_time:10m severity:ERROR', limit=10)` to inspect the relevant logs
3. **Extract** the `trace_id` from error logs (REQUIRED — look for the `trace_id` field)
4. **Call** `mcp_mcp_obs_traces_get(trace_id=<extracted_id>)` to inspect the full trace
5. **Summarize** the findings, citing BOTH log evidence AND trace evidence with the trace ID

### When the user asks about errors or system health:
1. Start with `mcp_mcp_obs_logs_error_count(minutes=<time_window>)` to see if there are any recent errors
2. If errors exist, use `mcp_mcp_obs_logs_search` to inspect the relevant logs
3. **Extract trace_id from logs** — this is REQUIRED for correlation
4. Use `mcp_mcp_obs_traces_get(trace_id=<id>)` to inspect the full trace
5. **Report the trace ID and trace details in your response**

### When the LMS backend returns errors (404, 500, etc.):
**ALWAYS** investigate with observability tools before concluding:
1. Call `mcp_mcp_obs_logs_error_count(minutes=10)` to check for backend errors
2. Search logs with `mcp_mcp_obs_logs_search(query='_time:10m service.name:"Learning Management Service"', limit=10)`
3. Look for the root cause (e.g., database connection failures)
4. **Extract the trace_id** from error logs
5. Fetch the trace to see the full failure path

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
- **ALWAYS include the Trace ID** — when you find errors, you MUST report the trace_id from the logs
- **ALWAYS fetch and describe the trace** — call `mcp_mcp_obs_traces_get` and report what operations failed
- **Actionable insights** — if you find an error, suggest what might be wrong (e.g., "PostgreSQL appears to be down")

## Required Response Format for Errors

When you find errors, your response MUST include:
1. **Error count** — how many errors found
2. **Time window** — what time period you searched
3. **Service name** — which service had errors
4. **Trace ID** — the trace_id from the error logs (**REQUIRED**)
5. **Trace details** — what the trace shows (operation, duration, error tags)
6. **Root cause** — what failed and why

## Example Interaction

**User:** "Any LMS backend errors in the last 10 minutes?"

**You:**
1. Call `mcp_mcp_obs_logs_error_count(minutes=10)` to check for errors
2. If errors exist, call `mcp_mcp_obs_logs_search(query='_time:10m service.name:"Learning Management Service" severity:ERROR', limit=10)`
3. Extract the `trace_id` field from log entries (e.g., `"trace_id": "8c0fe1c356c5120e24f775478d2ed63a"`)
4. Call `mcp_mcp_obs_traces_get(trace_id=8c0fe1c356c5120e24f775478d2ed63a)` to get full trace
5. Respond with this format:

```
Yes, I found **2 errors** in the LMS backend in the last 10 minutes.

**Error Details:**
- Service: Learning Management Service
- Error: Database connection failed — "Name or service not known"
- Operation: db_query (SELECT on item table)

**Trace Evidence:**
- Trace ID: `8c0fe1c356c5120e24f775478d2ed63a`
- Failed operation: `connect` to PostgreSQL
- Duration: 28ms
- Error tag: `socket.gaierror: [Errno -2] Name or service not known`

**Root Cause:** PostgreSQL database is unreachable. The backend cannot connect to the database service.

**Recommendation:** Check if PostgreSQL container is running.
```

## Important Notes

- Always use scoped time windows (e.g., "last 10 minutes") to avoid returning stale data
- Filter by `service.name` when investigating a specific service
- Use `severity:ERROR` to find error-level logs
- **The trace_id field is present in all error logs** — extract it and use it to fetch the trace
- If no errors are found, report that the system appears healthy
