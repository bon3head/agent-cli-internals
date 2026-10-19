# Eureka log

Chronological breakthroughs from the three deep-dive swarms, distilled from the lane scratchpads and `~/workspace/rea-reports/prose-expansion.md`. Shortform by design — each entry carries the exact command, offset, or pattern that cracked the surface, so any finding can be re-derived.

> **Landscape correction (2026-10-18 ~11:10 PM ET):** entries below that frame Fable 5/5.1 or
> GPT-6 Astra as unreleased are superseded. Fable 5 launched publicly 2026-06-09, Fable 5.1
> on 2026-09-01, GPT-6 Astra on 2026-09-03. **Mythos 5/5.1 is the genuinely non-public family**
> (Project Glasswing restricted). The string-level findings stand; only the public-vs-internal
> framing was wrong. See `findings/claude-code/10-fable-mythos.md`.

## 2026-10-18 (all times ET)

### 21:55 — agy, all lanes
Every lane verifies the target sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef` before touching anything. Two lanes lose /tmp scratch to a tmpfs wipe mid-run — lesson recorded: keep scratch in `~/workspace/`.

### 21:55–22:00 — agy A6: pclntab cracked
Stock Go parser fails: `NO VALID PCLNTAB FOUND` (textStart=0). Magic scan → candidate table at `0x1512750`, nfunc=164366, non-upstream header. Brute-force 30 (functab-offset × funcoff-anchor) combos → exactly one validates (functab = base + pclnOff, funcOff relative to that blob). Sample idx 82183 resolves to a real symbol. The Google-internal go1.28 layout is fingerprinted.

### 21:55–22:0x — claude C6: 41MB bundle found
Text-fraction window scan finds the contiguous bundle blob; binary search pins both ends: `0xbd00000–0xe41c000`. Then a single `chunk-d5as4466` occurrence at `0x588df71`, read in context, cracks the manifest entry pattern `name\0\0<kind:u8>\0\0\x80<u32le>` → 1,965 entries parsed. Five dead hypotheses on the u32 semantics documented and killed along the way.

### 22:02 — agy A1: the control plane documented itself
Embedded skill doc at strings-offsets 421532–421542 contains the literal curl recipe: `ANTIGRAVITY_LS_ADDRESS:=localhost:5387`, `/healthz`, `/exa.language_server_pb.LanguageServerService/$1`, `x-codeium-csrf-token` header. The 341-method ConnectRPC plane was documented by the binary itself.

### 22:05 — claude C3: first-party MCP hosts
`grep -aob -E '[a-z0-9-]+\.mcp\.claude\.com'` → gmail.mcp.claude.com + gcal.mcp.claude.com at offsets 97644414/97644441/224435318. `dd` @224434800 reveals the verbatim blocked-hosts array `["microsoft365.mcp.claude.com","gmail.mcp.claude.com","gcal.mcp.claude.com"]`.

### 22:05 — claude C5: model-catalog anchor
`{$schema:"https://downloads.claude.ai/model-catalog/v1/schema.json"` at offset 215173117 → brace-depth walk with string/escape tracking → full signed seed (v1468, issued 2026-10-01). Second registry at 199521935 → 21 models; `best:"fable"` at 199537503.

### 22:06–22:07 — agy A6: GO_TEXT_BASE calibrated without disassembly
textStart=0 blocks address calibration; moduledata hunt finds a hashed integrity manifest instead (Google-internal, not upstream). Prologue histogram (`49 3b 66 10` over .text in 1MB buckets, ~1s) → Go-dense region; first hit at `0x61d4300` preceded by INT3 padding = GO_TEXT_BASE. Cross-check `0x61d4300 + maxEntryOff` lands exactly at end of Go region.

### 22:10 — agy A1: sidecar blueprint
Embedded Node bundle at offsets 42035611–42041734: constructor reads `ANTIGRAVITY_LS_ADDRESS` / `ANTIGRAVITY_CSRF_TOKEN` / `ANTIGRAVITY_SIDECAR_WEB_PORT`; `#validateToken` at 42041996 matches `req.headers['x-sidecar-token'] || url.searchParams.get('token')` vs `ANTIGRAVITY_SIDECAR_UI_TOKEN`; `BIND_HOST = '127.0.0.1'` at 42035173 with a code comment warning against a routable bind. A token-authenticated local HTTP agent handle falls out of the strings.

### 22:10 — agy A2: the binary IS the skill corpus
`~/.gemini/antigravity-cli/builtin/skills/` found on disk. Marker-anchored carve + content-based end trim (after walk-back/forward over-grabs against interleaved chroma lexer XML) → 12 clean carves with exact rodata offsets (52.4KB total). Diff vs disk: 10/12 byte-identical.

### 22:10 — claude C2: string-mining at scale
`python re.findall(rb'[ -~]{6,}')` on the 244MB binary → 521,976 runs in 13s. Lane adopts ±350-char windowed-context mining via `re.finditer` after `grep -o` truncation keeps destroying minified-JS context. This method note paid off in every later extraction.

### ~22:14 — agy A6: FetchConfigFromAICode anomaly
Region disassembles as non-Go prologues at validated addresses; parser exonerated six ways (incl. `_func.entryOff` match). Toolchain codegen quirk for that package — flagged open, not blocking.

### 22:15 — claude C2: the `gs` flag-compatibility matrix
Decoding the `gs` object yields the full cloud flag-treatment matrix: refused / silently-dropped / client-only / forwarded-at-create. Every cloud flag's fate is now enumerated.

### ~22:20–22:25 — codex A: the protocol documents itself
`codex app-server generate-json-schema --out <dir>` emits 291 schema files: 95 client→server methods, 10 server→client requests, 75 notifications (counts script-verified, not hand-counted). The 95/10/75/1 asymmetry itself is the finding: heavily client-driven, fat streaming tail, tiny mandatory reverse-RPC channel (approval handlers) the client MUST answer or the agent stalls.

### ~22:20 — codex A: v2-over-v1 framing
v2 = current method namespace (`thread/*`, `turn/*`, `fs/*`, `command/exec*`, `mcpServer/*`, `config/*`, `account/*`, `skills/*`, `plugin/*`); v1 = legacy handshake + 10 approval callbacks carrying legacy `conversationId`/`callId` fields. You speak v2 methods over a v1 handshake.

### ~22:20 — codex A: no `"jsonrpc": "2.0"`
`JSONRPCRequest.json` requires only `["id", "method"]` — properties `id`, `method`, `params`, `trace`. A client mandating the version field fails on the wire.

### ~22:20 — codex A: schema as fossil record
Doc-comments leak intended-but-unshipped methods (`process/spawn`, `thread/turns/list`) — planned surface, not just live surface.

### ~22:25 — codex B: ConfigToml via serde FIELDS
97/101 top-level config keys recovered in declaration order from packed serde field-name literals, validated by element counts and adjacency pairs. Plus the eureka: the app-server schema's `ConfigReadResponse.json` embeds the typed resolved Config verbatim (e.g. `WebSearchMode: [disabled, cached, indexed, live]`).

### ~22:30 — codex C: auth surface
`account/login/start` takes `apiKey | chatgpt | chatgptDeviceCode | chatgptAuthTokens | amazonBedrock`. Device-code is a separate login type, not a flag. `chatgptAuthTokens` is marked `[UNSTABLE] FOR OPENAI INTERNAL USE ONLY` — a direct token-injection vector. The `https://chatgpt.com/oauth/codex/client.json` false positive (looks like a login endpoint, belongs to MCP OAuth client registration) is killed by surrounding-string context. Refresh grant is `urn:ietf:params:oauth:grant-type:jwt-bearer` + `assertion` — JWT-bearer flow, not standard `refresh_token`. Client IDs are self-redacting format strings: scrubbed at compile time, not merely absent.

### ~22:30 — codex C: rate-limit reset credits are redeemable
`account/rateLimitResetCredit/consume` is idempotency-keyed with outcomes `reset | nothingToReset | noCredit | alreadyRedeemed`. Quota management is not just read-only — there is a redeem path. `account/rateLimits/updated` is a sparse-merge push; refetching on every update is wasteful by schema contract.

### ~22:30 — codex D: the host is Rust+V8, not a JS runtime
`codex-code-mode-host` (69MB) strings are full of V8 JIT tier names (maglev, sparkplug, turbofan). It is a Rust binary embedding V8 (rusty_v8 v8-150.4.0) that executes raw JS "cells" over length-framed stdio or tonic gRPC. Both binaries share prost-generated `codex.code_mode.v1.rs` from the same build path (`codex-rs/target/.../codex-code-mode-protocol-362ee48cace341f3/out/`). Tool calls are delegated back to the main process (`SubscribeToToolCalls` + `tool/invoke`) — the sandbox is thin, policy lives in the main binary. The 2026-10-09 "Code Mode is unavailable" incident was host-*resolution*, not a flag question (`code_mode` = model-facing tool surface vs `code_mode_host` = binary wiring; `code_mode_only` is the latent all-tools-through-cells value).

### ~22:30 — codex E: telemetry correction
Two pipelines, not one: analytics ON by default (kill switch `[analytics] enabled = false`; metrics default endpoint `https://ab.chatgpt.com/otlp/v1/metrics` byte-exact in `otel/src/provider.rs`; per-turn `codex.turn.cost_microusd`, `codex.turn.token_usage`), OTel OFF by default (opt-in; `exporter = "none"` is absence of configuration, which is why no opt-out flag exists). `OTEL_SDK_DISABLED` has zero hits — the kill-switch operators reach for first silently does nothing. This corrects the earlier pass's imprecise "no opt-out found."

### ~22:30 — codex F: intel haul
`guardian_subagent` is an `ApprovalsReviewer` enum seat (`"user" | "auto_review" | "guardian_subagent"`) — an AI approving/denying tool calls instead of the user. `guardianv2` watches transcripts (`tool_calls`, `tool_outputs`, `reasoning`). Memories = distillation pipeline (`raw_memories.md` → `rollout_summaries/*.md` → `# Task Group` MEMORY blocks; `memories_v2_1.sqlite`), not a vector store. Token budgets are enforced via SQLite trigger firing auto-compaction. `sol` doubles as a model codename AND a voice name. GPT-5.4 is already retired in-binary (`GPT-5.4 is no longer available — Codex now uses GPT-5.6 Terra`), and an anti-hallucination guardrail literally says: `do not invent a separate gpt-6-pro model slug`.

### ~22:30 — codex D: cooperative async via Wait/yield
The `Pending/Yielded/Completed/Terminated` state machine plus `Wait`/`yield`: a cell can yield (`inputYielded`) and the client blocks on `Wait` until resume/complete — how long-running JS meets the turn loop. Main binary's `wait_handler.rs`: "Waits on a yielded `-` cell and returns new output or completion."

## 2026-10-19 (early AM)

### 01:54 — agy A3: GetTokenBase is a name-trap
Looked like an auth endpoint; surrounding strings show context-window budget accounting (`GetMaxTokenBase`, `GetRemainingBudget`, `GetCustomizationTokenBase`). Real auth: `HasAuthToken` + host-bridge `GetOAuthToken`. Recorded as a trap because it will catch the next person too.

### 01:58 — claude C1: 33 hook events
Quoted-enum-array regex `(?:\"([A-Za-z0-9_]+)\",){4,}\"...\"` yields the master list: 33 events, 19 beyond the known 14 (PostToolBatch, UserPromptExpansion, StopFailure, PreModelSwitch/PostModelSwitch, PermissionDenied, Setup, TeammateIdle, TaskCreated, Elicitation/ElicitationResult, ConfigChange, WorktreeCreate/Remove, InstructionsLoaded, CwdChanged, FileChanged, DirectoryAdded, MessageDisplay) plus a new `http` hook type (joining `command`, `prompt`, `mcp_tool`, `agent`).

### 02:05–02:06 — claude C1: permission engine byte-confirmed
Rule validator `Twe()` body quoted at file offset 199006950, then the runtime decision engine: deny > ask > allow > passthrough, first-match per tier, `decisionReason:{type:"rule"}`. `Write(path)` / `NotebookEdit(path)` / `Glob(path)` rules are NEVER matched by file checks (validator warning, not a silent match); `:*` is Bash-only; `bypassPermissions` is ignored from project/local settings (repo-controllable).

### ~02:1x — claude C1: settings schema builder
69KB function `Ia()` at file offset 199028346 → 199 typed settings keys (zod types + describes). `.passthrough()` discovery explains why unknown keys never error. Five sources, low→high precedence: user → project → local → `--settings` flag → managed (server-managed > MDM > `/etc/claude-code/managed-settings.json` on Linux).

### ~02:05 — agy A5: assembled safety config
Embedded assembled monitors config at strings-line 1611062 (16.5KB) with header: `# Source: per_monitor/*/ + profiles/antigravity.textproto`, `# Regenerate: blaze run //gdm/security/agi_control/agent_monitoring/monitors/config:assemble`, `# Checksum: sha256:caeb48770b7a4df5d910608adeeacb73441f9ddf5e273ee61a11cd5676f5342f`. Three monitors, all `EXECUTION_PHASE_PRE_TOOL`: `agy_tool_safety` (allowlist, LOG), `sir_flash_lite` (flash-lite triage, LOG), `severe_internal_risks_agy` (flash reviewer, BLOCK, 10.7KB rubric). Safety runs per-step, not sampled; config is server-overridable. Resolves a prior-art unknown.

### ~02:15 — agy A5: lineage, three independent angles
`codeium_common_pb` under `google3/third_party/jetski` + `bevin@codeium.com` (offset 346102) + `exa.*` proto namespace vs `third_party/jetski` build dir → Windsurf/Codeium lineage confirmed.

### ~02:20 — agy A5: 4-tier model waterfall + BYO path
`FetchAvailableModels` (google.internal.cloud.code.v1internal) → 4-tier resolution: inline admin_settings → remote catalog → gateway discovery → built-in. `MODEL_PLACEHOLDER_M*` enum M0..M1650 contiguous; 39-entry alias map decoded. `AGY_LLM_GATEWAY_*` env vars (URL, key, headers, CA, proxy, per-tier models, wire protocol) = the sanctioned bring-your-own-model path.

### 09:55 — agy A4: the claimed eureka that wasn't
`--disable_telemetry` "verified" via `agy --disable_telemetry --help` exit 0. Coordinator control: `agy --bogus-flag-xyz --help` also exits 0 (`--help` short-circuits parsing). Strict tests — `agy --disable_telemetry models`, `--disable-telemetry models`, `--disable_telemetry=true models` — all exit 2, `flags provided but not defined`. A `DisableTelemetry` field exists in a CLI options struct in rodata; wiring UNVERIFIED. Lesson: existence claims about flags need a real subcommand, never `--help`.

## 2026-10-18 ~22:35–23:00 — trial phase

- 17/17 agy trials CONFIRMED (4 PoCs exit 0; refutation holds: `--disable_telemetry models` → exit 2).
- 13 CONFIRMED + 1 PARTIAL for claude (`claude mcp list` hangs on live health checks; exit 124 at timeout 20 — functions, unbounded).
- 8/8 codex trials CONFIRMED — with a version surprise: PATH `codex` is 0.149.0 (`/opt/hatch-image/bin/codex`), not the 0.155.1 repair; the REA schema/feature-flag baselines are a 0.149.0 capture, and `gpt-6-astra` (19 strings hits, live catalog entry in 0.155.1) is absent from 0.149.0. Doctor flags 0.163.0 available.
- Byte anchors re-verified: pclntab 164,366/19,312; MCP blocked-hosts array, model-catalog seed, and registry anchors all byte-exact on the live binaries.

## Standing lessons

1. Read the binary's own documentation first. Twice the richest surface (agy's curl recipe, codex's schema generator) was printed on the box.
2. Controls beat claims. The `--disable_telemetry` refutation and the gateway correction both came from running the control experiment, not from more strings.
3. Name-traps are real (`GetTokenBase`). Verify the semantics before writing up the surface.
4. For Go and Bun targets, format-aware extraction (pclntab parsing, string-table carving) beats disassembly on every axis: speed, memory, and completeness.
5. Kill weak findings in writing, with the evidence for the kill. A documented kill is a finding.
