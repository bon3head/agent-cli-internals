# 04 — 33 hook events, 5 hook types (C1)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C1 (settings/permissions) · **Trial status:** no live PoC trial (no trial PoC covers hooks);
CONFIRMED at the byte level in REA.
**Confidence:** CONFIRMED (byte-level). A sibling 19-item list also naming `StatusLine` and `FileSuggestion`
exists (noted, unresolved).

---

## 1. WHAT WAS FOUND

The hook system is a full event bus: **33 events** (master enum `kg`), 19 beyond the commonly
documented 14. The new ones: `PostToolBatch`, `UserPromptExpansion`, `StopFailure`,
`PreModelSwitch`/`PostModelSwitch`, `PermissionDenied`, `Setup`, `TeammateIdle`, `TaskCreated`,
`Elicitation`/`ElicitationResult`, `ConfigChange`, `WorktreeCreate`/`WorktreeRemove`,
`InstructionsLoaded`, `CwdChanged`, `FileChanged`, `DirectoryAdded`, `MessageDisplay`.

Subsets (CONFIRMED): **16 matcher-capable** (matcher regex applies): UserPromptSubmit,
UserPromptExpansion, PreToolUse, PermissionRequest, PermissionDenied, PostToolUse,
PostToolUseFailure, PostToolBatch, SubagentStart, SubagentStop, TaskCreated, TaskCompleted,
Elicitation, ElicitationResult, WorktreeCreate, WorktreeRemove. **11 blocking-capable**
(`continue:false` / `decision:"block"`): PreToolUse, PostToolUse, PostToolUseFailure,
PostToolBatch, UserPromptSubmit, UserPromptExpansion, Stop, StopFailure, SubagentStart,
SubagentStop, PermissionDenied. 21 events carry `session_id` on stdin.

Key stdin shapes (all from the `hook_event_name:x("…")` schemas):
- `PostToolUse` carries `duration_ms` ("Tool execution time in milliseconds. Excludes
  permission-prompt and hook time") and `tool_response`.
- `PostToolBatch`: `tool_calls[]` — "Fired once after every tool call in a batch has
  resolved… PostToolUse fires per-tool and may run concurrently… exactly once with the full batch."
- `SessionStart`: `source` ∈ `startup|resume|clear|compact|fork`, `model?`, `agent_type?`;
  its output can set `watchPaths[]` ("Absolute paths to watch for FileChanged hooks") and
  `reloadSkills` ("Re-scan skill and command directories").
- `InstructionsLoaded`: `file_path`, `memory_type` ∈ `User|Project|Local|Managed`,
  `load_reason` ∈ `session_start|nested_traversal|path_glob_match|include|compact`.
- `Elicitation`: `mcp_server_name`, `message`, `mode?` ∈ `form|url` — fired when an MCP
  server requests user input.
- `FileChanged`: `file_path`, `event` ∈ `change|add|unlink`; `CwdChanged`: `old_cwd`, `new_cwd`;
  `ConfigChange`: `source`, `file_path?`.

Five hook types (discriminated union on `type`, CONFIRMED from `_p()`):
- `command`: shell/exec hook. `timeout?` (default 15s), `async?`, `asyncRewake?` (background,
  wakes the model on **exit code 2**), `once?`, `statusMessage?`, plus `if` (permission-rule
  filter, e.g. `"Bash(git *)"`) on every type.
- `prompt`: model-evaluated hook; `$ARGUMENTS` = hook input JSON; `continueOnBlock?` (NEW:
  "Sets the continue value for the decision:\"block\" produced when ok is false. Default false
  (turn ends)").
- `mcp_tool` (literal `"mcp_tool"`, not `"mcp"`): `server`, `tool`, `input?` with
  `${path}` interpolation from hook input JSON (e.g. `"${tool_input.file_path}"`).
- **`http` (NEW)**: `url` (required), `headers?` with `$VAR_NAME` interpolation gated by
  `allowedEnvVars[]` (required for any env interpolation); allowlisted by settings
  `allowedHttpHookUrls` ("If empty array, no HTTP hooks are allowed. Arrays merge across
  settings sources") and intersected with `httpHookAllowedEnvVars`.
- `agent`: spawns a subagent hook (`model?` default Haiku).

New hook output fields: `defer` in `permissionDecision` (`allow|deny|ask|defer`),
`decision: approve|block` (not just "block"), `terminalSequence` ("A terminal escape
sequence (e.g. OSC 9 / OSC 777 desktop-notification) for Claude Code to emit on your
behalf. Only notification/title OSCs (0, 1, 2, 9, 99, 777) and BEL are permitted; anything
else is dropped"), `retry` (PermissionDenied), `watchPaths`/`reloadSkills` (SessionStart),
`additionalContext`/`classifierContext` (PostToolUse), `suppressOriginalPrompt`
(UserPromptSubmit), `displayContent` (MessageDisplay — replaces the delta on screen without
changing the stored message).

## 2. HOW IT WAS FOUND

- Lane C1: a quoted-enum-array regex (`(?:\"([A-Za-z0-9_]+)\",){4,}\"..."`) yielded the
  33-event master list — 19 events beyond the known 14 (`scratchpad-c1.md`, 01:58).
- All stdin JSON shapes extracted from the `hook_event_name:x("…")` schema definitions and
  dumped to `hook-schemas.txt`; the five hook-type schemas dumped from `_p()`
  (`~/workspace/rea-claude/deep-dive/hook-schemas.txt`).
- Matcher semantics byte-confirmed: the matcher is compiled as a JavaScript RegExp
  (`"Invalid regex pattern in hook matcher: "`); `if` accepts permission-rule syntax
  (`"Permission rule syntax to filter when this hook runs (e.g., \"Bash(git *)\")"`).

## 3. WHAT IT UNLOCKS

In plain terms: hooks are not "run a linter after edits" anymore. There is a real event bus —
file changes, directory changes, config changes, model switches, MCP elicitation requests —
each arriving as structured JSON on stdin. That is the wiring for reactive local tooling:
something that watches a directory and acts, something that notices the config changed and
re-syncs, something that answers an MCP server's question programmatically.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Reactive recipes (JSON shapes confirmed):**
  - `FileChanged` → `{"file_path": ..., "event": "change|add|unlink"}`: arm `watchPaths` from
    a `SessionStart` hook response, then run formatters/linters only on changed files.
  - `ConfigChange` → `{"source": ..., "file_path?": ...}`: reload local policy/tooling state
    when any settings file is edited.
  - `CwdChanged` → `{"old_cwd": ..., "new_cwd": ...}`: re-arm per-project hooks on directory
    switches.
  - `Elicitation` → `{"mcp_server_name": ..., "message": ..., "mode": "form|url"}`:
    answer MCP server input requests programmatically via the output
    `{"action": "accept|decline|cancel", "content": ...}`.
  - `PostToolBatch`: aggregate analytics — fires exactly once per batch after all parallel
    tool calls resolve (unlike per-tool PostToolUse).
- **HTTP hooks:** set `allowedHttpHookUrls: ["https://hooks.example.com/*"]` plus
  `httpHookAllowedEnvVars` in settings, then declare hooks of type `http` to fan events to a
  local/remote endpoint — no shell process needed.
- **Async wake:** `asyncRewake: true` runs a hook in the background and wakes the model on
  exit code 2 — the pattern for long-running watchers that need to report back.
- **Blocking:** `PreToolUse` output `{"permissionDecision": "allow|deny|ask|defer"}` lets a
  hook make the permission call itself; `defer` means "let the normal flow decide."
