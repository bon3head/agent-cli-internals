# 07. MCP: CLI serves itself; first-party endpoints expanded (C3)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C3 (MCP/plugins) · **Trial status:** CONFIRMED live
(`pocs/extract_mcp_plane.py` re-run → `first-party blocked hosts: ['microsoft365.mcp.claude.com',
'gmail.mcp.claude.com', 'gcal.mcp.claude.com']`, 3 first-party + 5 third-party URLs;
`pocs/verify_poc.py` → `PASS: all 35 ground-truth items present; kills hold`;
byte anchor @224435288 re-read live → byte-exact;
**PARTIAL:** `claude mcp list` ran with `timeout 20` → printed only `Checking MCP server
health…`, killed at exit 124: it performs live health checks; do not run in automation
without a timeout wrapper)
**Confidence:** CONFIRMED (byte-level). slack.mcp.claude.com's auth path and
mcp-proxy.anthropic.com's exact role are INFERENCE.

---

## 1. WHAT WAS FOUND

- **`claude mcp serve` starts the Claude Code MCP server**: the CLI is its own MCP server.
  10 subcommands (`claude mcp --help`, live): `add`/`add-json`/`add-from-claude-desktop`/
  `get`/`list`/`login`/`logout`/`remove`/`reset-project-choices`/`serve`. **No
  `enable`/`disable`** (contrast `plugin`).
- Transports (CONFIRMED, binary transport registry `var bnt={stdio:…,sse:…,http:…,
  "streamable-http":…,ws:…,sdk:…,"claudeai-proxy":…}`): `stdio`, `sse`, `http`,
  `streamable-http`, `ws`, `sdk`, `claudeai-proxy`, plus `sse-ide`, `ws-ide`.
  CLI `add` exposes only stdio/sse/http; `ws` only via `add-json`.
- **New first-party hosts** (byte-exact array @224435288, `chunk-w51ahvvb.js`):
  ```js
  var p=["microsoft365.mcp.claude.com","gmail.mcp.claude.com","gcal.mcp.claude.com"];
  ```
  `gmail.mcp.claude.com` and `gcal.mcp.claude.com` are new vs prior art. Local OAuth is
  refused for these three ("…is Anthropic-hosted and doesn't support local OAuth. Connect
  it via Settings → Connectors on claude.ai"), overridable via
  `tengu_mcp_local_oauth_blocked_hosts` (offsets 97644385 region / 224435288).
  `slack.mcp.claude.com/mcp` is first-party but **not** in the blocked array
  (INFERENCE: supports local OAuth or a legacy path).
- `.mcp.json` upward-walk discovery (cwd → filesystem root) with `${ENV_VAR}` expansion,
  symlink refusal, size limit; wrapped and unwrapped formats accepted. Approval flow:
  unapproved servers show `⏸ Pending approval`, never connected; rejected via
  `disabledMcpjsonServers`. Config scopes: `user`, `project`, `local`, `dynamic`
  (programmatic-only), `managed`, `enterprise`.
- **MCP tools are permission-ruleable** (CONFIRMED). Tool naming: `mcp__${server}__${tool}`
  where server normalization is `e.replace(/[^a-zA-Z0-9_-]/g,"_")`; plugin-bundled:
  `mcp__plugin_<plugin>_<server>__<tool>`. Rule syntax (byte-exact quote): "An allow pattern
  must name the scope it widens: globs are permitted only in the tool position after a
  literal mcp__<server>__ prefix. Deny and ask rules accept wildcards anywhere."
- MCP OAuth: Dynamic Client Registration, OAuth callback listener with state validation
  (`"Invalid state parameter"`), issuer-stamped persisted creds (SEP-2352),
  `mcp-needs-auth-cache.json`. `claudeai-proxy`-type servers authenticate through the
  claude.ai identity, not per-server OAuth.
- Elicitation: 102 hits, modes `form`|`url`; permission event subtype carrying
  `mcp_server_name`, `message`, `mode`. Servers may declare `headers` or a `headersHelper`
  **command** that produces headers at runtime (consent/sha256-gated like marketplace
  commands).
- PoC: `pocs/extract_mcp_plane.py` emits the endpoint/marketplace inventory → JSON + MD
  (red-green verified against 35 ground-truth items; kills hold).

## 2. HOW IT WAS FOUND

- Lane C3: `strings -n 6` dump (521,975 lines) + `grep -aob -E '[a-z0-9-]+\.mcp\.claude\.com'`
  → gmail.mcp.claude.com + gcal.mcp.claude.com at offsets 97644414/97644441/224435318;
  `dd` @224434800 revealed the verbatim blocked-hosts array.
- Classifier `T1` (transport/type resolution) and server normalization `Tn` recovered from
  the strings dump; transport registry `bnt` located by searching `claudeai-proxy":b8r`;
  `.mcp.json` discovery walk found via `while(ne!==Me)` code region reads.
- Trial (2026-10-18): `extract_mcp_plane.py` → `first-party urls: 3, third-party urls: 5`;
  `verify_poc.py` → `PASS: all 35 ground-truth items present; kills hold`; the
  @224435288 anchor re-read byte-exact (`...mcp.claude.com"];function i(e){return
  e.toLowerCase().replace(/\.$/,"")}function u(){let e=C("tengu_mc…`).

## 3. WHAT IT UNLOCKS

In plain terms: the MCP plane is fully scriptable; you can manage servers from the command
line, point the CLI at your own endpoints, and (biggest deal) the CLI itself can *be* an MCP
server for other agents and tools to call. It is the cleanest integration seam found in the
binary.

## 4. HOW A DEVELOPER BUILDS ON IT

- **CLI-as-MCP-server:** `claude mcp serve`: embed Claude Code as a tool source inside
  other agents, editors, or pipelines via the standard MCP transports (stdio/SSE/HTTP/
  WebSocket). The exposed toolset was not enumerated (LIMITATION): enumerate against
  `serve` in a follow-up before building on specific tools.
- **Endpoint inventory:** `pocs/mcp-plane-inventory.json` + `.md`: the complete first-party
  (blocked OAuth hosts, proxy, slack) and third-party (asana, figma, linear, sentry, box)
  endpoint list, regenerated from any build.
  ([mcp-plane-inventory.md](sandbox://workspace/rea-claude/deep-dive/pocs/mcp-plane-inventory.md))
- **Permission recipes for MCP:** allow needs the literal server prefix
  (`mcp__github__*`); deny/ask accept wildcards anywhere (`mcp__*`);
  `--allowedTools "mcp__github_inline_comment__create_inline_comment"` works verbatim.
  Enterprise layer: `allowedMcpServers` / `deniedMcpServers` (deny wins) / `allowManagedMcpServersOnly`.
- **Operational warnings:** `claude mcp list` performs live health checks: wrap in
  `timeout` and never run in automation loops (trial: killed at 20 s, exit 124).
  `claude mcp login <name>` supports `--no-browser` for headless OAuth; `add` supports
  `-e KEY=val`, `-H "K: V"`, `--scope local|user|project`, and `${ENV_VAR}` expansion in
  `.mcp.json`.
