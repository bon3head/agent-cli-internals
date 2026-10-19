# 09. MCP is a first-class citizen with a future protocol version negotiated in-code

**Version pin:** method inventory from the **0.149.0** schema set; per-server config struct
(`RawMcpServerConfig`, 28 fields) and the `MCP-Protocol-Version: 2026-07-28` negotiation
strings from the **0.155.1** binary. Live MCP server connections were not made (UNVERIFIED).

## 1. WHAT WAS FOUND

MCP is wired through config, the app-server protocol, and a version-negotiation code path:

**Per-server config, `RawMcpServerConfig` (28 fields, 0.155.1 strings):** recovered fields
include `command`, `url`, `bearer_token` / `bearer_token_env_var`, `oauth`, `scopes`,
`startup_timeout_*`, `supports_parallel_tool_calls`, `environment_id`. Managed via
`codex mcp add` into the config file (the exact config-table name was unconfirmed from
strings: lane B notes `mcp_servers` is not a top-level `ConfigToml` field; use the CLI).
The binary also carries `CODEX_MCP_PROTOCOL_VERSION` with an explicit error
`(unsupported CODEX_MCP_PROTOCOL_VERSION \``.

**App-server methods (0.149.0 schema, CONFIRMED):**
- `mcpServer/tool/call{threadId, server, tool, arguments?: JsonValue, _meta?}`: call an MCP tool
- `mcpServer/resource/read{threadId?, originCallId?, server, uri, connectorId?}`: read an MCP resource
- `mcpServer/oauth/login{name, threadId?, clientRegistration?, scopes?, timeoutSecs?}`: start MCP server OAuth login
- `mcpServerStatus/list{cursor?, limit?, detail?, threadId?}`: MCP server inventory
- `config/mcpServer/reload`: reload MCP server config without restart

**Reverse-RPC:** `mcpServer/elicitation/request{threadId, turnId?, serverName, mode:
form|openai/form|openaiForm|url, message, requestedSchema (or url+elicitationId)}`: the
server asks the *client* to fill a form or run a URL flow on behalf of the MCP server.
Completion arrives as `mcpServer/oauthLogin/completed{name, threadId?, success, error?}`;
startup status pushes via `mcpServer/startupStatus/updated{threadId?, name, status, error?, failureReason?}`.

**Future protocol version negotiated in-code (0.155.1, CONFIRMED):** the binary sends the
header `MCP-Protocol-Version: 2026-07-28`; `InputRequiredResult requires negotiated
protocol version 2026-07-28 or newer`; `legacy MCP endpoint does not support
server/discover`; feature flag `mcp_2026_07_28` (under development, false in the 0.149.0
inventory). The new version gates `server/discover` and elicitation v2
(`InputRequiredResult`). The related `ModelProviderInfo` field
`supports_standalone_web_search` shows search becoming a per-provider capability rather
than a global tool.

**Hosted MCP evidence:** `https://serpi.openai.com/v1` appears in `Starting MCP
serpi.openai.com/v1`, a hosted SERP-as-MCP server. `https://chatgpt.com/oauth/codex/client.json`
is fetched for **MCP** OAuth client registration ("MCP authorization server does not
advertise CIMD with token endpoint auth method `none`"): the earlier lane-C false positive
that attributed it to the login flow was killed by context.

**CONFIRMED vs INFERENCE:** the 28-field config struct (name + sampled fields), the five
app-server methods, the elicitation reverse-RPC, the 2026-07-28 negotiation literals, and
the serpi endpoint are CONFIRMED. That any third-party MCP server will work against the
2026-07-28 negotiation, and live OAuth/elicitation round-trips, are UNVERIFIED.

## 2. HOW IT WAS FOUND

Lane B (config strings: `RawMcpServerConfig` field-name literals in the 0.155.1 binary;
`codex mcp --help` for the management surface) + Lane A (method inventory from the 0.149.0
schema set, `mcpServer/*` branches) + Lane F (internal-intel: the 2026-07-28 negotiation
literals and flag, serpi URL). Kill record: `chatgpt.com/oauth/codex/client.json` was
initially attributed to login; the surrounding MCP-OAuth-client-registration strings killed
that attribution.

## 3. WHAT IT UNLOCKS

Any MCP server (local stdio, remote HTTP, OAuth-protected) can be registered once and
driven through the same typed protocol as everything else: tool calls, resource reads,
OAuth login, hot config reload, and startup-status streams. Because the protocol version is
negotiated in-code, Codex already speaks a *future* MCP version (2026-07-28) with server
discovery and richer elicitation, so tooling built against these findings won't be
surprised when that version ships. And OpenAI's own search stack is exposed as an MCP
server you can connect to.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Register a server: `codex mcp add` (writes into config.toml; prefer the CLI over
   hand-editing since the table name is unconfirmed from strings). Per-server knobs:
   `command` (stdio) or `url` (HTTP), `bearer_token`/`bearer_token_env_var` for static
   tokens, `oauth` + `scopes` for OAuth servers, `startup_timeout_*` for slow starters,
   `supports_parallel_tool_calls`, `environment_id`.
2. Drive it over the app-server: `mcpServerStatus/list` to verify it started (watch
   `mcpServer/startupStatus/updated`), then `mcpServer/tool/call{threadId, server, tool,
   arguments}` / `mcpServer/resource/read{server, uri}`.
3. Implement the reverse-RPC `mcpServer/elicitation/request` handler (Finding 02) if your
   servers use elicitation: render `mode: form` via `requestedSchema`, or open the `url`
   flow, and reply with the elicitation result.
4. MCP OAuth: `mcpServer/oauth/login{name, scopes?}` and wait for
   `mcpServer/oauthLogin/completed`.
5. Hot-reload after config changes: `config/mcpServer/reload`; no app-server restart.
6. Version-proofing: pin expectations to negotiated protocol versions; the binary already
   requires ≥2026-07-28 for `InputRequiredResult` and `server/discover`, so servers that
   only speak older MCP drafts will fail those calls.
7. Protocol version override exists: `CODEX_MCP_PROTOCOL_VERSION` env (unsupported values
   error loudly: fail-fast, not silent).
