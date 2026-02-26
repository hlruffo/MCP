# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv pip install -e .

# Run the app (default: uses mcp_server.py automatically)
uv run main.py

# Run with additional MCP server scripts
uv run main.py extra_server.py

# Test MCPClient in isolation (runs a quick tool call against mcp_server.py)
uv run mcp_client.py
```

The `.env` file controls runtime behavior:
- `ANTHROPIC_API_KEY` — required
- `CLAUDE_MODEL` — required (e.g. `claude-sonnet-4-5`)
- `USE_UV` — set to `1` when running with uv (affects how the MCP server subprocess is launched)

There is no test runner or linter configured.

## Architecture

The app is a CLI chat client that connects to one or more MCP servers over stdio transport, then uses Claude (via the Anthropic API) to answer user queries with access to those servers' tools.

### Request flow

```
CliApp (prompt_toolkit UI)
  └─> CliChat.run(query)          # parses @doc mentions and /commands
        └─> Chat.run(query)       # agentic tool-use loop
              ├─> Claude.chat()   # Anthropic API call
              └─> ToolManager     # dispatches tool_use blocks to MCPClients
```

### Key files

| File | Role |
|---|---|
| `main.py` | Entry point. Launches `mcp_server.py` as a subprocess, wires up clients, creates `CliChat` + `CliApp`. |
| `mcp_server.py` | FastMCP server exposing tools (`read_doc_contents`, `edit_document`) and resources (`docs://documents`, `docs://documents/{doc_id}`). In-memory `docs` dict acts as the document store. |
| `mcp_client.py` | `MCPClient` — async context manager wrapping an MCP `ClientSession` over stdio. Methods: `list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `read_resource`. |
| `core/chat.py` | `Chat` base class. Implements the agentic loop: calls Claude, handles `tool_use` stop reason by dispatching to `ToolManager`, repeats until `end_turn`. |
| `core/cli_chat.py` | `CliChat(Chat)`. Overrides `_process_query` to expand `@doc_id` mentions into `<document>` XML and handle `/command doc_id` prefixes via MCP prompts. |
| `core/cli.py` | `CliApp` — prompt_toolkit REPL with `UnifiedCompleter` (Tab-completes `/commands` and `@resources`) and inline `CommandAutoSuggest`. |
| `core/claude.py` | Thin wrapper around `anthropic.Anthropic`. Exposes `chat()` with optional tools, system prompt, thinking mode. |
| `core/tools.py` | `ToolManager` — discovers which `MCPClient` owns a given tool name, executes tool calls, and returns `ToolResultBlockParam` lists. |

### MCP server ↔ client contract

- The server runs as a child process; the client communicates over stdin/stdout using the MCP stdio transport.
- Resources use the `docs://` URI scheme. `docs://documents` returns JSON `list[str]`; `docs://documents/{doc_id}` returns `text/plain`.
- Prompts are not yet implemented in `MCPClient` (`list_prompts` and `get_prompt` return empty lists) — this is a known TODO.

### Adding to the server

- **New tool**: decorate a function with `@mcp.tool(name=..., description=...)` in `mcp_server.py`.
- **New resource**: use `@mcp.resource("scheme://path")`.
- **New prompt**: use `@mcp.prompt(name=...)` — then implement `list_prompts` / `get_prompt` in `MCPClient`.
- **Extra MCP server**: pass its script path as a CLI argument to `main.py`; it will be launched with `uv run <script>` and registered as a named client.
