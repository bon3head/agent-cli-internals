# 12 — Hidden flags and aliases (C2/C3)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C2 (cloud/hidden flags), C3 (`mcp list`) · **Trial status:**
- `claude --help` live check → CONFIRMED the visible surface (`--cloud`, `gateway`, `mcp`, `plugin`, `ultrareview`)
- `claude mcp list` → **PARTIAL** (`timeout 20 claude mcp list`: stdout `Checking MCP server health…` only,
  exit 124 — it performs live health checks; functions but no inventory retrievable within 20 s)
**Confidence:** CONFIRMED (byte-level). `--watch-artifact`'s exact URL/slug argument shape and
`CLAUDE_CODE_HOST_GATEWAY_LINEAGE` semantics are INFERENCE/ungrounded.

---

## 1. WHAT WAS FOUND

Flags and behaviors hidden from `--help` (byte-confirmed, with the help-hiding mechanism seen
in the flag registry — `.hideHelp()`, and the `p` set of recognized non-help flags):

- **`--remote` = hidden alias of `--cloud**`: binary flag-validation code `r=e.cloud??e.remote`.
  Not shown in `--help`.
- **`--pool` = alias of `--environment**` (`ccpool_…` self-hosted environments).
- **`--attach-serve`**: expects `cse_…` session ids —
  `"Error: --attach-serve expects a session id (cse_...)"`; cannot combine with
  `--cloud/--remote`.
- **`--watch-artifact`**: requires an interactive session —
  `"Error: --watch-artifact requires an interactive session (not print mode, --sdk-url,
  --init-only, or redirected output)"`. Injects a system message: "The user started this
  session watching the artifact (\\S+) (via claude --watch-artifact)". Watch states:
  `connecting` (handshake not finished), `disarmed`, `auto-replies stopped (the user can ask
  to resume)`. Variant: `--watch-artifact-no-autoreact` (INFERENCE: takes an artifact
  URL/slug).
- **`--await-claim`**: binds a pre-warmed spare process ("a process started with
  --await-claim in a neutral directory with the host-level options") to its session:
  relocates it to cwd, applies per-session prompt options and in-process MCP server set,
  starts SessionStart hooks. Constraints: requires `--print` with
  `--input-format=stream-json` and `--output-format=stream-json`; cannot combine with
  `--continue/--resume/--fork-session`; refused for cloud sessions (local SDK-host only).
- **`--client-data-url <url>`**: "URL for a signed configuration document. Claude Code exits
  if it cannot load it or it does not cover the selected model." Env form
  `CLAUDE_CODE_CLIENT_DATA_URL` keeps it out of the process list. Validation: "the URL must
  be the https://downloads.claude.ai/ address Anthropic gave you, exactly as given";
  unusable in cloud/remote-environment/ssh sessions; only works talking to the Anthropic API
  directly, not through Bedrock/Vertex/Foundry or a cloud gateway.
- **`claude mcp` has no `enable`/`disable`** (contrast `plugin enable/disable`).
- **`claude mcp list` does live health-checks at list time**: it hung >30s in REA and
  reproduced the hang in trial (20 s timeout, exit 124, only
  `Checking MCP server health…` printed). Approved servers are health-checked unless
  project-disabled; unapproved `.mcp.json` servers show as `⏸ Pending approval`, never
  connected.
- **KILL:** "`claude remote-control` has start/stop/status subcommands" — `--help` shows a
  single persistent-server command; lifecycle is `--continue`/`--session-id` plus bridge
  register/deregister (`/v1/environments/bridge`).

## 2. HOW IT WAS FOUND

- Lane C2: hidden flags found via the binary flag-registry (`p` set of recognized non-help
  flags, `.hideHelp()` markers) + windowed-context mining; the `--remote`/`--cloud` alias
  and `--pool`/`--environment` alias confirmed in flag-validation code
  (`r=e.cloud??e.remote`); `--watch-artifact` states and `--await-claim` claim protocol
  (`claim_session` control request; `not_claimed: ... discard it and start the session
  normally`) quoted verbatim from the strings.
- Lane C3: `claude mcp --help` live output (10 subcommands, no enable/disable); the
  `mcp list` hang reproduced live in both REA (>30 s, killed) and the trial
  (`timeout 20`, exit 124).

## 3. WHAT IT UNLOCKS

In plain terms: the CLI has a shadow control surface that the help text never shows — spare
process pre-warming for instant session start, artifact watching, remote aliases, signed
config documents. These are the levers for shaving seconds off session startup and for
controlling fleets that the public docs don't document.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Session-start latency:** `--await-claim` + stream-json is the documented pre-warm
  pattern — spawn spares in a neutral directory with host-level options, then `claim_session`
  binds one to a session on demand. Handle `not_claimed` by falling back to a normal start.
- **Fleet config pinning:** distribute signed config documents via
  `CLAUDE_CODE_CLIENT_DATA_URL` (env keeps it out of the process list); remember the URL
  must be the exact `https://downloads.claude.ai/` address and only works against the
  Anthropic API directly — not Bedrock/Vertex/Foundry/gateway, not cloud sessions.
- **Operational caution:** never call `claude mcp list` in automation without a `timeout`
  wrapper — it health-checks every approved server live (trial: 20 s, exit 124, no output).
  Use `--no-browser` for headless `claude mcp login`.
- **Alias hygiene:** prefer `--cloud` / `--environment` in scripts (aliases `--remote`,
  `--pool` are hidden and could move); validate session IDs against
  `^(?:session|cse)_[A-Za-z0-9_-]+$` and `cse_…` for `--attach-serve`.
