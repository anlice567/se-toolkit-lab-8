"""MCP server for observability tools."""

import asyncio
import os
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# VictoriaLogs API endpoint
VICTORIALOGS_URL = os.getenv("VICTORIALOGS_URL", "http://localhost:42010")
# VictoriaTraces API endpoint (Jaeger-compatible)
VICTORIATRACES_URL = os.getenv("VICTORIATRACES_URL", "http://localhost:42011")

server = Server("mcp-obs")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available observability tools."""
    return [
        Tool(
            name="logs_search",
            description="Search logs in VictoriaLogs using LogsQL query. Returns matching log entries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "LogsQL query, e.g., '_time:10m service.name:\"Learning Management Service\" severity:ERROR'",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of log entries to return",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="logs_error_count",
            description="Count errors per service over a time window in VictoriaLogs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "minutes": {
                        "type": "integer",
                        "description": "Time window in minutes to search for errors",
                        "default": 60,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="traces_list",
            description="List recent traces for a service from VictoriaTraces.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name to filter traces",
                        "default": "Learning Management Service",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of traces to return",
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="traces_get",
            description="Fetch a specific trace by ID from VictoriaTraces.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "The trace ID to fetch",
                    },
                },
                "required": ["trace_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[Any]:
    """Execute an observability tool."""
    import json
    from mcp.types import TextContent

    async with httpx.AsyncClient(timeout=30.0) as client:
        if name == "logs_search":
            query = arguments.get("query", "_time:10m")
            limit = arguments.get("limit", 20)
            url = f"{VICTORIALOGS_URL}/select/logsql/query"
            params = {"query": query, "limit": limit}
            response = await client.post(url, params=params)
            response.raise_for_status()
            # VictoriaLogs returns newline-delimited JSON
            lines = response.text.strip().split("\n")
            results = []
            for line in lines:
                if line.strip():
                    try:
                        results.append(json.loads(line))
                    except json.JSONDecodeError:
                        results.append({"raw": line})
            return [TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "logs_error_count":
            minutes = arguments.get("minutes", 60)
            query = f"_time:{minutes}m severity:ERROR"
            url = f"{VICTORIALOGS_URL}/select/logsql/query"
            params = {"query": query}
            response = await client.post(url, params=params)
            response.raise_for_status()
            lines = response.text.strip().split("\n")
            error_count = 0
            service_counts: dict[str, int] = {}
            for line in lines:
                if line.strip():
                    error_count += 1
                    try:
                        entry = json.loads(line)
                        service = entry.get("service.name", "unknown")
                        service_counts[service] = service_counts.get(service, 0) + 1
                    except json.JSONDecodeError:
                        pass
            result = {
                "total_errors": error_count,
                "time_window_minutes": minutes,
                "by_service": service_counts,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "traces_list":
            service = arguments.get("service", "Learning Management Service")
            limit = arguments.get("limit", 10)
            url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces"
            params = {"service": service, "limit": limit}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            # Jaeger API returns {"data": [...]}
            traces = data.get("data", [])
            summary = []
            for trace in traces:
                summary.append(
                    {
                        "trace_id": trace.get("traceID"),
                        "spans": len(trace.get("spans", [])),
                        "start_time": trace.get("startTime"),
                    }
                )
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]

        elif name == "traces_get":
            trace_id = arguments["trace_id"]
            url = f"{VICTORIATRACES_URL}/select/jaeger/api/traces/{trace_id}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            # Jaeger API returns {"data": [trace]}
            traces = data.get("data", [])
            if not traces:
                return [TextContent(type="text", text=f"Trace {trace_id} not found")]
            trace = traces[0]
            # Summarize the trace
            spans = trace.get("spans", [])
            span_summary = []
            for span in spans:
                span_info = {
                    "span_id": span.get("spanID"),
                    "operation_name": span.get("operationName"),
                    "service_name": span.get("process", {}).get(
                        "serviceName", "unknown"
                    ),
                    "duration_ms": span.get("duration", 0) / 1000,
                    "tags": {
                        tag["key"]: tag["value"]
                        for tag in span.get("tags", [])
                        if tag.get("key") in ["error", "http.status_code", "event"]
                    },
                }
                span_summary.append(span_info)
            result = {
                "trace_id": trace.get("traceID"),
                "spans": span_summary,
            }
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            raise ValueError(f"Unknown tool: {name}")


async def _async_main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


def main():
    """Entry point for mcp-obs CLI."""
    asyncio.run(_async_main())


if __name__ == "__main__":
    main()
