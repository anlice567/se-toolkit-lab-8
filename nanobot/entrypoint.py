#!/usr/bin/env python3
"""
Entrypoint for nanobot gateway in Docker.

Resolves environment variables into the config at runtime,
then launches nanobot gateway.
"""

import json
import os
from pathlib import Path


def main():
    # Paths
    config_dir = Path("/app/nanobot")
    config_path = config_dir / "config.json"
    workspace_dir = config_dir / "workspace"
    resolved_config_path = config_dir / "config.resolved.json"

    # Read base config
    with open(config_path, "r") as f:
        config = json.load(f)

    # Override provider settings from env vars
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Override gateway settings from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host:
        config["gateway"]["host"] = gateway_host
    if gateway_port:
        config["gateway"]["port"] = int(gateway_port)

    # Configure MCP servers with env vars
    mcp_servers = config.get("tools", {}).get("mcpServers", {})

    # LMS MCP server
    if "lms" in mcp_servers:
        lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
        lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")
        if lms_backend_url:
            mcp_servers["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = lms_backend_url
        if lms_api_key:
            mcp_servers["lms"]["env"]["NANOBOT_LMS_API_KEY"] = lms_api_key

    # Webchat MCP server
    if "webchat" in mcp_servers:
        webchat_relay_url = os.environ.get("NANOBOT_WS_URL")
        webchat_token = os.environ.get("NANOBOT_ACCESS_KEY")
        if webchat_relay_url:
            mcp_servers["webchat"]["env"]["NANOBOT_WS_URL"] = webchat_relay_url
        if webchat_token:
            mcp_servers["webchat"]["env"]["NANOBOT_WS_TOKEN"] = webchat_token

    # Webchat channel settings
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")

    if "webchat" in config.get("channels", {}):
        if webchat_host:
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port:
            config["channels"]["webchat"]["port"] = int(webchat_port)

    # Write resolved config
    with open(resolved_config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_config_path}")

    # Launch nanobot gateway
    os.execvp(
        "nanobot",
        [
            "nanobot",
            "gateway",
            "--config",
            str(resolved_config_path),
            "--workspace",
            str(workspace_dir),
        ],
    )


if __name__ == "__main__":
    main()
