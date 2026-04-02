"""Entry point for running mcp_obs as a module: python -m mcp_obs"""

import asyncio

from mcp_obs.server import main

asyncio.run(main())
