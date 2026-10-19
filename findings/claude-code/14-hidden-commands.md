# 14. Hidden commands + unregistered `claude daemon` + child-session flag forwarding

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287` · carved JS `~/workspace/rea-claude/deep-dive/carved/claude-bundle-full.js`
(offsets below are carved-bundle offsets)

---

## 1. WHAT WAS FOUND

13 hidden commands (absent from `claude --help`, all marked `{hidden:!0}`), plus one command that is not
registered in commander at all: `claude daemon` is intercepted by an argv pre-scan before the parser runs.
Separately, a 9-flag forward subset (`CQ()`) is the exact flag list propagated when the CLI spawns child
sessions.

The 13 (10 found by the `.command("X",{hidden:!0})` regex, independently reproduced; 3 in alternate
syntactic forms):

| Command | What it does (from bundle description strings) |
|---|---|
| `edit-permission-rules` | Apply one permission-rule edit read as JSON from stdin (used by the VS Code extension) |
| `edit-memory-settings` | Apply one memory-settings edit read as JSON from stdin (used by the VS Code extension) |
| `edit-skill-overrides` | Apply one skill state edit read as JSON from stdin (used by the VS Code extension) |
| `edit-sandbox-settings` | Apply one sandbox settings edit read as JSON from stdin (used by the VS Code extension) |
| `edit-hook` | Apply one hook edit read as JSON from stdin (used by the VS Code extension) |
| `edit-chrome-settings` | Apply one Claude in Chrome settings edit read as JSON from stdin (used by the VS Code extension) |
| `drop-worktree-registrations` | Drop deleted worktrees' git registrations named as JSON on stdin (used by the VS Code extension) |
| `design-login` | Run the Claude Design sign-in, or report its state, as JSON lines (used by the VS Code extension) |
| `remote-control` (alias `rc`) | Control local sessions from claude.ai/code or the Claude mobile app; renders its own custom help (`claude remote-control --help`, USAGE/OPTIONS format, not commander) |
| `apply-project-settings` | Review how this folder's settings files differ from the version accepted for cloud sessions, and accept them (name resolved: `wjt="apply-project-settings"`; needs a terminal) |
| `sandbox` | Print the effective sandbox posture (enabled, source, strict mode, filesystem policy, Bash auto-allow) + Windows install state as one JSON line; has a visible subcommand `install` |
| `import-conversations <exportPath>` | Options `--cwd <dir>` (archive anchor), `--dry-run`; emits error `import-conversations is not enabled` when gated |
| `plugin test [dir]` | desc from `hw.test.description`; `.allowUnknownOption().allowExcessArguments(!0)` with custom help formatter |

The `edit-*` family is the VS Code extension's stdin-JSON control surface; each refuses hand use
("it is run by the VS Code extension, not by hand"). `remote-control --help` executes live, proving
hidden != unusable. Root help lists 18 visible commands: none of the 13 appear.

`claude daemon`: the argv pre-scan `function d2o(t){let i=0;while(t[i]==="--dangerously-skip-permissions"||t[i]==="--allow-dangerously-skip-permissions")i++;return t[i]==="daemon"?t.slice(i+1):null}`
skips leading permission-bypass flags, then if the first real arg is `daemon`, slices argv there and
dispatches to the daemon controller. `daemon` never appears as `.command("daemon")` (0 hits), so it has
custom arg handling: subcommands `run [json-path]` / `status` / `logs` / `uninstall` / `stop [--any]
[--keep-workers]`; options `--json-path <p>` (default `~/.claude/daemon.json`), `--log-file <p>`
(default `~/.claude/daemon.log`). Help notes: "Service install is disabled in this version; the daemon
runs on demand and exits when the last client disconnects."

`CQ()`: the child-session forward subset (verbatim body):

```
function CQ(t){return[...t.settings?["--settings",t.settings]:[],
...t.managedSettings?["--managed-settings",t.managedSettings]:[],
...t.pluginDir.flatMap((i)=>["--plugin-dir",i]),
...t.pluginDirNoMcp.flatMap((i)=>["--plugin-dir-no-mcp",i]),
...t.addDir.flatMap((i)=>["--add-dir",i]),
...t.mcpConfig.flatMap((i)=>["--mcp-config",i]),
...t.settingSources!==void 0?[`--setting-sources=${t.settingSources}`]:[],
...t.strictMcpConfig?["--strict-mcp-config"]:[],...t.restricted?["--restricted"]:[]]}
```

9 flags: `--settings`, `--managed-settings`, `--plugin-dir`, `--plugin-dir-no-mcp`, `--add-dir`,
`--mcp-config`, `--setting-sources=<csv>`, `--strict-mcp-config`, `--restricted`. Everything else
(model choice, thinking mode, permission mode, API keys) is deliberately NOT inherited by spawned
children.

## 2. HOW IT WAS FOUND

Tool: `grep -aob` + `dd` on the carved bundle; `claude --help` diff (read-only).

```
grep -ao '\.command("[a-z-]*",{hidden:!0})' claude-bundle-full.js | wc -l
# → 10
grep -ao '\.command("[a-z-]*",{hidden:!0})' claude-bundle-full.js \
  | sed 's/.*command("//;s/".*//' | sort -u
# → design-login drop-worktree-registrations edit-chrome-settings edit-hook
#   edit-memory-settings edit-permission-rules edit-sandbox-settings edit-skill-overrides
#   remote-control sandbox
# (+3 alternates: apply-project-settings @17532120 region [var wjt=],
#  import-conversations @17534233, plugin test [hw.test.description @18482162])

dd if=claude-bundle-full.js bs=1 skip=60950 count=700
# → ...Sources}}function CQ(t){return[...t.settings?["--settings",t.settings]:[], ...
#   (full verbatim body above; CQ at carved 60959 / binary 198241823)

dd if=claude-bundle-full.js bs=1 skip=61440 count=400
# → ...]}function d2o(t){let i=0;while(t[i]==="--dangerously-skip-permissions"
#   ||t[i]==="--allow-dangerously-skip-permissions")i++;
#   return t[i]==="daemon"?t.slice(i+1):null}
#   (d2o at carved 61446 / binary 198242310; grep -aob 'function d2o(' → 198242310 binary)
```

Offset note: an earlier lane draft cited CQ @61540 / d2o @61581 from a superseded carve (boundary
shift ~135–581 B). The offsets above are from the current carve, re-read by hand.

## 3. WHAT IT UNLOCKS

The CLI you see in `--help` is a showroom; the real machine has a service entrance. The 13 hidden
commands are how the VS Code extension quietly edits your settings, hooks, permissions, and sandbox
policy without opening a dialog: one JSON line on stdin at a time. `claude daemon` is a background
supervisor that spawns background sessions and scheduled tasks, and it deliberately bypasses the normal
command parser so it can tolerate `--dangerously-skip-permissions` up front. And the 9-flag forward
list is the "trust boundary" for spawning: when the CLI clones itself into a child session, it carries
over settings and plugin paths but drops everything else, which is why a child process can't silently
escalate to a different model or permission mode than its parent.

## 4. HOW A DEVELOPER BUILDS ON IT

- Script the `edit-*` control surface yourself: `echo '{"...":...}' | claude edit-permission-rules` uses
  the same JSON contract as the VS Code extension: automate settings edits without touching files by
  hand (validate by diffing the settings file before/after).
- `claude sandbox` prints the effective sandbox posture as one JSON line: use it in CI to assert the
  posture you expect before a run starts.
- `claude daemon status` / `claude daemon logs` give you the supervisor's view of background sessions;
  `~/.claude/daemon.json` is the config file (0600-ish writes), `~/.claude/daemon.log` the log.
- When spawning child sessions via the SDK, audit against the `CQ()` 9-flag list: anything not in it
  must be re-supplied explicitly to the child: this is the exhaustive allowlist, not a heuristic.
- `remote-control` is the documented way to drive local sessions from claude.ai or the mobile app;
  `claude remote-control --help` is the live reference (custom help, not commander).
