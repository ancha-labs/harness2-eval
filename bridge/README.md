# Experimental MCP stdio bridge

The recorded runs used **Ancha CLI 0.1.4 with this bridge**. Ancha 0.1.5 ships native MCP endpoints for the same four twins, Slack, GitHub, Datadog and PagerDuty, configured with `ancha mcp config`. Those native endpoints were not used in these runs.

[tools-mcp.ts](tools-mcp.ts) exposes the scenario's existing [native-SDK tools](../scenario/tools.ts) over line-delimited MCP JSON-RPC on stdin/stdout. It supports initialization, ping, tool listing and tool calls. The four API URL environment variables must resolve to `127.0.0.1`, `localhost` or `[::1]`; other hostnames are rejected. The bridge uses Ancha-provided twin credentials and no model key.

[probe-agent.py](../adapter/probe-agent.py) configures OpenCode to launch the bridge with Node 24. Install the scenario lockfile dependencies using `npm ci --prefix scenario`. The imported SDK tool module lives beside that dependency tree, so Node resolves the same packages after the bridge was moved to this directory.

This is a minimal experiment transport with the method and protocol subset used in the study. It is not the Ancha 0.1.5 native MCP implementation. Its only source change is the relative import of the relocated scenario tool file. See [reproduction commands](../README.md#reproduce).
