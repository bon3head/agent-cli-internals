# MCP & Plugin Control-Plane Inventory
_Extracted 2026-10-19T02:41:13.205971+00:00 from `/home/hatch/.local/share/claude/versions/2.1.287` (244317368 bytes), read-only, zero network._

## First-party endpoints

### Anthropic-hosted OAuth-blocked hosts (`tengu_mcp_local_oauth_blocked_hosts`)
- `microsoft365.mcp.claude.com`
- `gmail.mcp.claude.com`
- `gcal.mcp.claude.com`

### First-party URLs found in binary

- `https://mcp-proxy.anthropic.com`
- `https://microsoft365.mcp.claude.com/mcp`
- `https://slack.mcp.claude.com/mcp`

### Third-party MCP URLs found in binary

- `https://mcp.asana.com/sse`
- `https://mcp.box.com`
- `https://mcp.figma.com/mcp`
- `https://mcp.linear.app/sse`
- `https://mcp.sentry.dev/mcp`

## Transports

`stdio`, `sse`, `http`, `streamable-http`, `ws`, `sdk`, `claudeai-proxy`, `sse-ide`, `ws-ide`

## Config scopes

`user`, `project`, `local`, `dynamic`, `managed`, `enterprise`

## Settings keys (with occurrence counts)

- `enabledPlugins` x186
- `allowedProviders` x94
- `allowedMcpServers` x64
- `strictKnownMarketplaces` x62
- `deniedMcpServers` x51
- `blockedMarketplaces` x46
- `disabledMcpjsonServers` x32
- `strictMcpConfig` x31
- `enabledMcpjsonServers` x26
- `enableAllProjectMcpServers` x19
- `allowManagedMcpServersOnly` x14
- `plugin_marketplaces` x2
- `tengu_mcp_local_oauth_blocked_hosts` x2

## Plugin sources

- `claude-code-marketplace`
- `claude-plugins-official`
- `builtin`
- `skills-dir`
- `claudeai`

## Marketplace protocol markers

- plugin_marketplaces settings key (git repo default)
- GCS primary fetch, git fallback
- marketplace as npm package
- manifestSha256 trust pin
- installationPreference: available|required|auto_install|not_available
- headersHelper runtime header command
- MCPB bundled server bundle
- DXT (Desktop Extension) bundle

## Plugin manifest fields (`manifest.<field>` references)

`channels`, `description`, `homepage`, `hooks`, `lspServers`, `mcpServers`, `name`, `repository`, `userConfig`, `version`

## Permission-rule evidence (byte-exact quotes)

> globs are permitted only in the tool position after a literal mcp__<server>__ prefix. Deny and ask rules accept wildcards any
> Use 'mcp__<server>' to deny one server's tools

## Kills (verified absent)

- recommendedPlugins: absent — settings key absent in 2.1.287
- sharePlugin: absent — no plugin-share surface
- pluginShare: absent — no plugin-share surface
- plugin share: absent — no plugin-share surface (checked case-insensitive, 0 hits)
