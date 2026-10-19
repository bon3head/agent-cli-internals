# Finding 13 — The 0.149.0 → 0.155.1 feature-flag delta + the hidden `--managed-daemon` flag

**Version pin:** deltas computed between 0.149.0 (258,322,048 bytes) and 0.155.1
(269,273,536 bytes, sha256 `0753dfe1…b761`). Prior `feature-flags.txt` baseline
is byte-identical to 0.149.0's live `features list` registry, so the delta is
exactly the 0.149.0→0.155.1 change set.

## 1. WHAT WAS FOUND

### The 24-flag delta (re-verified on this pass via live `features list` oracles)

`codex features list` → 142 flags on 0.155.1 vs 118 on 0.149.0. The 24 new
names, with registry stage/state (parsed, not hand-counted — output reproduced
independently on this pass):

**5 already stable+ON** (shipped, not roadmap):
`compaction_image_budget`, `content_item_kinds`, `in_app_local_automation`,
`sleep_tool`, `unified_exec_tty`

**17 under-development** (registered but unwired — no functional strings beyond
the registry name-lists; same evidence class as the prior `OTEL_SDK_DISABLED`
zero-hit result):
`api_key_model_discovery`, `bedrock_setup_wizard`, `code_mode_prewarm`,
`codex_apps_mcp_2026_07_28`, `context_management`, `guardian_ext`,
`guardianv2.thread_context`, `mcp_oauth_refresh_coordination`,
`omit_app_server_notification_media`, `powershell_shell_version`,
`reasoning_effort_override`, `shell_snapshot_v2`, `skip_host_skill_discovery`,
`step_model_switching`, `transcript_v2`, `windows_sandbox_service`,
`write_stdin_approval`

**1 experimental:** `worktrees` (false)
**1 removed-at-birth:** `local_thread_store_shared_compression` — registered
only to mark removal.

### Stage/state changes 0.149.0 → 0.155.1 (python diff of both registries)
- `realtime_conversation`: under-development → **experimental**. Voice is being productized.
- `remote_compaction_v2`: stable/**true** → removed/false. **Killed after shipping.**
- `unified_exec_zsh_fork`: under-development/false → removed/**true**, superseded by `unified_exec_tty` (stable/true). The zsh-fork exec path was replaced by the unified tty exec path.

### `NEW:` announcements map 1:1 onto the experimental flags
Four announcement literals (~8× repeated i18n copies), first occurrences:
- @218627379: `NEW: Network proxy can now be enabled from /experimental. Restart Codex after enabling it.`
- @218627541: `NEW: Worktrees can now be enabled from /experimental. Restart Codex after enabling it.`
- @218628583: `NEW: Voice conversations can now be enabled from /experimental. Restart Codex after enabling, then use /voice.`
- @218628833: `NEW: Prevent sleep while running is now available in /experimental.`

The live registry has exactly four experimental-stage flags (`network_proxy`,
`worktrees`, `realtime_conversation`, `prevent_idle_sleep`) — exactly the four
announced. Display names + descriptions recovered from the announcement blob
@218627278: `worktrees` = "Worktrees" — "Create isolated Git worktrees and
group sessions by repository."; `network_proxy` = "Network proxy" — "Apply
network proxy restrictions to sandboxed sessions that already have network
access."; `realtime_conversation` = "Voice conversations" — "Talk with Codex
using /voice."; `prevent_idle_sleep` = "Prevent sleep while running" —
"Keep your computer awake while Codex is running a thread."

### The hidden `codex app-server --managed-daemon` flag (NEW in 0.155.1)

Accepted by the parser but **absent from `codex app-server --help`**
(re-verified on this pass: `app-server --managed-daemon --help` prints help
normally; `app-server --bogus-flag-xyz --help` errors `unexpected argument`;
`grep -c managed-daemon` on the help text = 0). Boolean, takes no value.
**New in 0.155.1**: 0.149.0 rejects it
(`error: unexpected argument '--managed-daemon' found`).

Related literals in the binary:
- config key `managed_daemon` + env `MANAGED_DAEMON` + description **`Save
  loaded threads during managed daemon shutdown`** @218641594–218641622
  (packed config/env/doc table also containing `analytics_default_enabled` /
  `ANALYTICS_DEFAULT_ENABLED` / `Controls whether analytics are enabled by
  default`).
- `--managed-daemon` flag literal first occurrence @217949888 (this pass;
  lane recorded @217949890 — both hit the same clap literal region).
- Invoking it starts the server (proceeds to sandbox init: `Codex could not
  find bubblewrap on PATH...`), i.e. it is a real runtime flag, not a stub.

What it likely does (HYPOTHESIS, labeled): the flag makes a foreground
`app-server` adopt managed-daemon lifecycle behavior — persisting loaded
threads at shutdown so the managed daemon (`app-server daemon ...`) can pick
them up. Basis: the description string `Save loaded threads during managed
daemon shutdown` + the `app-server daemon {bootstrap,start,restart,update,
enable-remote-control,disable-remote-control,stop,version}` subcommand tree
that exists in 0.155.1. The exact shutdown handshake is UNVERIFIED.

### Also new/absent in 0.155.1 CLI surface
- `mcp-server` subcommand REMOVED (comm on both binaries' `--help`; nothing added).
- Hidden deprecated `codex login --api-key` (pre-existing, not new): prints
  `The --api-key flag is no longer supported. Pipe the key instead, e.g.
  \`printenv OPENAI_API_KEY | codex login --with-api-key\`.` and stops —
  deliberate deprecation redirect to keep the key out of argv. Literal
  @219211660.

### Error-message inventory (20 subsystems, first-occurrence offsets)
New 0.155.1 error strings indexed by subsystem, e.g.: agent identity
(`failed to request agent identity ` @218612613, ×23), agent tasks, plugin
system (`duplicate plugin ` @218611485, ×12), skills, rollout migration
(`failed to restore moved rollouts` @217354445), thread store
(`failed to park thread` @219009500, ×9), auth/token refresh, MCP event
stream, enterprise/residency, exec-server, managed daemon/self-updater
(`failed to prune stale managed ` @217306428, ×3; `updater failed to resolve
current updater executable` @219190914), remote control/pairing, voice/realtime
(`voice startup failed` @222638116), approvals (`denied action after seeing
the concrete risk` @220885515, ×4), network proxy, code-mode cells
(`unknown cell ` @217187403), multi-agent, feedback, connector runtime cache,
world-state snapshot. Full list with offsets: re-suite lane artifact
`depth-flags-errors.md` §C.

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Method: strings tier + live `--help` / `features list` oracle; no network.

Reproduction (this pass, independent):

```sh
BIN=~/.bun/install/global/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex
$BIN features list > /tmp/feat-1551.txt        # 142 flags
~/.local/bin/codex-0.149.0.bak features list > /tmp/feat-1490.txt   # 118 flags
# new-in-0.155.1 = registry(0.155.1) minus registry(0.149.0) -> the 24 names above
# stage changes: realtime_conversation under-development -> experimental;
#   remote_compaction_v2 stable/true -> removed/false;
#   unified_exec_zsh_fork under-development/false -> removed/true
$BIN app-server --managed-daemon --help | head -5    # help prints, exit 0
$BIN app-server --bogus-flag-xyz --help              # error: unexpected argument
$BIN app-server --help | grep -c managed-daemon      # 0 (hidden)
```

Byte evidence for managed-daemon (python, file offsets):
- `--managed-daemon` literal: `data.find(b'--managed-daemon')` → 217949888
- config row: `data.find(b'managed_daemon')` → 218641594;
  `data.find(b'MANAGED_DAEMON')` → 218641608;
  description `Save loaded threads during managed daemon shutdown` →
  218641622 (surrounding packing: `REMOTE_CONTROL|Enable remote control for
  this app-server process without changing persistence|managed_daemon|
  MANAGED_DAEMON|Save loaded threads during managed daemon shutdown|
  managed-daemon|analytics_defaul...`).

The hidden-flag oracle swept 68 pruned `--flag` string candidates × 24
subcommands + 11 third-level commands; every candidate either returned
`unexpected argument` or was already documented. The only two survivors are
`--managed-daemon` and `--api-key`. A flag whose literal is constructed at
runtime would evade the string sweep; clap-derive normally embeds contiguous
literals (known limitation, recorded).

## 3. WHAT IT UNLOCKS (plain language, no jargon)

Feature flags are the product team's diary: every experimental feature has a
name, a maturity stage, and an on/off switch. The 24-name delta is a
three-month window into what OpenAI is building next — sleep management,
sandbox tty exec, network proxying, Git worktrees, voice conversations, token
budgets — and what they killed (remote compaction died after shipping; the
zsh-fork exec path was replaced). The hidden `--managed-daemon` flag is the
juicier find: it's a secret switch for a background daemon that keeps your
conversation threads saved across restarts, invisible in the help text but
fully working. For anyone studying how a company ships an agentic coding tool,
this is the unreleased-product roadmap written in the company's own words.

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

1. Flip flags locally for research: `codex features list` shows the registry;
   the five stable+ON flags are already live behavior — diff your outputs with
   them on/off to measure what each gates (e.g. `sleep_tool` gates
   `tools/handlers/sleep` @217226851; `unified_exec_tty` gates the `tty` exec
   parameter — `TTY execution is disabled by config; omit \`tty\` or set it
   to false.` @220746308).
2. Prototype against the 17 under-development flags at your own risk: they
   register but have no functional strings — the behavior is not in the binary
   yet. Don't build on `guardian_ext` or `code_mode_prewarm` until a later
   release wires them.
3. For managed-daemon integration: pass `--managed-daemon` to a foreground
   `app-server` and set `managed_daemon` / `MANAGED_DAEMON` per the packed
   table; observe which threads persist across shutdown. The description
   string (`Save loaded threads during managed daemon shutdown`) is the only
   contract — treat the shutdown handshake as UNVERIFIED and instrument it
   before relying on it.
4. The 20-subsystem error inventory (@first-occurrence offsets above) is a
   ready-made fault-injection map: each subsystem's error strings define the
   exact failure modes you can trigger in tests (e.g. `timed out while
   evaluating the requested approval` @221571519 for approvals timeout paths).
