# 07. Full hook contract extracted (6 events, protojson stdin/stdout)

> **Correction (2026-10-19, reinforcement):** downgraded from "7 events" to **6** — four independent
> hunts found no 7th event; the "7" had no provenance in the lane artifacts. The 6 named events are
> VERIFIED; telemetry enums additionally list pre/post-turn and compaction hook *types*.

**Trial status:** CONFIRMED at suite level (17/17 on the same binary). Not separately re-trialed; stands on lane A2 evidence (byte-exact carve of the embedded `docs/hooks.md`).

---

## 1. WHAT WAS FOUND

The complete lifecycle-hooks contract was carved from the binary's embedded `docs/hooks.md` (offset 95255018 → 95268147, 13,129 bytes: the largest embedded customization doc) and is **byte-identical** to the on-disk copy. Summary (CONFIRMED):

- **File:** single `hooks.json` in the customization root (e.g. `.agents/hooks.json`). Top-level keys = hook **names** → event config. Working dir for commands = the directory containing `hooks.json`. Commands run via `sh -c` (Unix) / `cmd /c` (Windows); `~` expanded. Only `type: "command"` supported; hooks run **synchronously and block the agent loop**.
- **Per named hook:** `enabled` (bool, default true) + event arrays.
- **Events (6 names, 7 with telemetry enum coverage):** `SessionStart` (once per session), `PreToolUse`, `PostToolUse`, `PreInvocation`, `PostInvocation`, `Stop`. Telemetry enums also list pre/post-turn and compaction hook types.

**Per-event stdout contracts (all keys camelCase protojson):**

| Event | Stdout result |
|---|---|
| `PreToolUse` | `{decision: "allow"\|"deny"\|"ask"\|"force_ask", reason?, permissionOverrides?, overwrite?}`: `overwrite` = shallow top-level merge into the tool call's args; the agent is told which keys changed |
| `PostToolUse` | `{}` (input adds `toolCall{name,args}`, `stepIdx`, `error?`) |
| `SessionStart` / `PreInvocation` | `{injectSteps?}`: inject `systemMessage` (persists), `userMessage`, or `ephemeralMessage` (dropped after current turn) |
| `PostInvocation` | `{injectSteps?, terminationBehavior?}` where terminationBehavior ∈ `"force_continue"` \| `"terminate"` \| `""` |
| `Stop` | `{decision: "continue"\|…, reason?}`; input has `terminationReason` ∈ `NO_TOOL_CALL`, `MAX_INVOCATIONS`, `MAX_FORCED_INVOCATIONS`, `MAX_TOKEN_BUDGET_EXCEEDED`, `ERROR`, `USER_CANCELED`, `TERMINAL_STEP_TYPE`, `TERMINAL_CUSTOM_HOOK`, `INJECTED_RESPONSE` |

- **Matcher** (Pre/PostToolUse only): `"*"` = all tools; `"run_command"` = exact; `"run_command\|view_file"` = either; `"browser_.*"` = prefix. Tool names = step type lowercased minus `CORTEX_STEP_TYPE_` prefix.
- **Handler fields:** `type` (default `"command"`), `command` (**required**), `timeout` (int seconds, default 30).
- Input context keys include `conversationId`, `stepIdx`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath`, `modelName`.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A2 (config schema), strings tier. The hook doc was one of 12 embedded customization docs carved by marker-anchored carve (strings interleaved with chroma lexer XML + proto descriptors required content-based end trim; 21:58→22:28). Offsets validated; 10/12 carves byte-identical to disk copies, hooks.md among them.

---

## 3. WHAT IT UNLOCKS

The agent has tripwires you can install: small scripts that fire before a tool runs, after it finishes, when a session starts, or when the agent is about to stop. Before a tool runs, your script can allow it, deny it, ask the user, or even rewrite the tool's arguments, and the agent is told what you changed. When it stops, your script learns why (out of steps? budget hit? user canceled?) and can keep it going. That is a control panel over the agent's entire lifecycle, in JSON over stdin/stdout.

---

## 4. HOW A DEVELOPER BUILDS ON IT

```jsonc
// .agents/hooks.json  (or ~/.gemini/config/hooks.json for global)
{
  "lint-checker": {
    "PostToolUse": [
      { "matcher": "run_command",
        "hooks": [ { "type": "command", "command": "./scripts/lint.sh", "timeout": 10 } ] }
    ]
  },
  "safety-gate": {
    "enabled": false,
    "PreToolUse": [
      { "matcher": "run_command",
        "hooks": [ { "command": "./scripts/safety-check.sh" } ] }
    ]
  }
}
```

- Hook scripts read context JSON on **stdin**, write result JSON on **stdout**. All keys camelCase.
- `PreToolUse` returning `{"decision":"deny","reason":"..."}` blocks the tool; `overwrite` rewrites args with a shallow merge (nested objects replaced wholesale).
- `Stop` can return `{"decision":"continue"}` to resume the loop: mind `MAX_FORCED_INVOCATIONS` / `MAX_TOKEN_BUDGET_EXCEEDED` guards.
- Notes: working dir = the hooks.json directory; sync execution blocks the agent loop (keep handlers fast). Whether hooks fire identically for `agy -p` headless runs is unverified. Plugin-bundled hooks must sit at the plugin root (`hooks/hooks.json` is not discovered).
