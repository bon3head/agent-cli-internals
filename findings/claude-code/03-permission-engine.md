# 03 — Permission decision engine decoded (C1)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C1 (settings/permissions) · **Trial status:** CONFIRMED live
(`pocs/c1-permission-matcher.py` re-run → `ALL PASS`, 32/32 rule checks)
**Confidence:** CONFIRMED (byte-level). Check-time rule-list assembly order is INFERENCE (tier dominance
is byte-confirmed); executable-basename resolution and path case-sensitivity are marked INFERENCE.

---

## 1. WHAT WAS FOUND

The permission engine is a deterministic first-match pipeline. Decision order, byte-confirmed in
`Zt()`/`Le()` @220571591:

```js
if(m[0]!==void 0)return{behavior:"deny",...};
if(h[0]!==void 0)return{behavior:"ask",...};
if(y[0]!==void 0)return{behavior:"allow",...};
return{behavior:"passthrough",...} // "This command requires approval"
```

**deny > ask > allow > passthrough**, first matching rule per tier, with
`decisionReason:{type:"rule"}` on every hit. Byte-level details:

- Rule validator `Twe(e,n)` @199006950: a rule is `Tool` (bare) or `Tool(content)`;
  `)` must be the last unescaped char. **Allow rules may not have wildcard tool names**
  (CONFIRMED: `Wbt`: `` `Wildcard tool name "${e}" is not supported in allow rules` ``).
  `:*` is Bash-prefix syntax only — `Edit(foo:*x)` is invalid (`'The ":*" syntax is only
  for Bash prefix rules'`).
- **File-tool aliasing gotcha** (CONFIRMED): `Write(path)`, `NotebookEdit(path)`, `MultiEdit(path)`
  rules are **never matched** by file permission checks — only `Edit(path)` rules are;
  `Glob(path)` rules never match — only `Read(path)`. Written them anyway → validation
  *warning* (not error): `` `${On(r)} is not matched by file permission checks — only
  ${c}(path) rules are. Use ... instead` ``. Bare `"Write"` / `"Glob"` (no path) still work.
- Bash rule matching (`yt()` @220570938, glob `$8()` @199003774), case-insensitive:
  exact (`Bash(npm run test)`), prefix (`Bash(git:*)` — bare `git` or `git ` with space
  boundary), wildcard (`Bash(npm run *)`, `*`→`.*`, `**/`→`/(?:.*/)?`). A trailing ` *`
  with exactly one star becomes `( .*)?`, so **`Bash(git *)` also matches the bare command `git`**.
- **Repo-controllable guard** (CONFIRMED): `bypassPermissions` and `auto` in
  `permissions.defaultMode` are **ignored from project/local settings** (`Kcs=["auto",
  "bypassPermissions"]`; `"only policy/user/flag settings may grant bypass mode
  (projectSettings and localSettings are repo-controllable)"`).
- **`allowDangerouslySkipPermissions` is NOT a settings key** (absent from all 199 schema
  keys) — CLI flag / VS Code IDE only. bypassPermissions also needs that consent; in
  non-interactive without consent the ignore is logged under
  `tengu_settings_bypass_unconsented_noninteractive_ignored`.
- `permissions.disableBypassPermissionsMode: "disable"` is the admin kill-switch.
- PoC: `pocs/c1-permission-matcher.py` — rule parser/validator + decision simulator that
  replicates the exact pipeline; 32/32 checks pass (incl. `Write(path) never matches`,
  `deny beats ask/allow`, globstar paths).

## 2. HOW IT WAS FOUND

- Lane C1: the rule validator `Twe()` body quoted at 199006950, then the runtime decision
  engine `perm-matcher.txt` extracted verbatim (see
  `~/workspace/rea-claude/deep-dive/perm-matcher.txt`).
- Bash matching recovered from `yt()` @220570938 plus the glob compiler `$8()` @199003774;
  tier order from `Zt()`/`Le()` @220571591; grant restriction from the `Kcs` array and
  surrounding strings in the 0xd640000–0xd8c0000 permissions window.
- Scratchpad: `scratchpad-c1.md`; trial re-run confirmed `ALL PASS` on 32 checks.
- INFERENCE labeled where it is: the merged check-time list is presumed to follow the same
  `_xe` assembly order as `buildPermissionRules` (tier dominance itself is byte-confirmed);
  executable-resolved matching is environment-dependent so the PoC matches the raw command.

## 3. WHAT IT UNLOCKS

In plain terms: permission behavior is no longer "let me run it and see what it prompts."
You can now simulate, offline and deterministically, exactly what a given
settings.json will allow, ask about, or deny — including the silent gotchas (the
`Write(path)` rule that looks right but never fires, the project-settings bypass that is
quietly ignored, the bare-`git` match).

## 4. HOW A DEVELOPER BUILDS ON IT

- **Offline simulator:** `python3 pocs/c1-permission-matcher.py` — feed it a rule set +
  tool call; it prints the winning tier and rule. Embed in onboarding flows ("does my
  allow-list open a hole?") or CI that diffs permission posture across machine images.
  ([pocs/c1-permission-matcher.py](sandbox://workspace/rea-claude/deep-dive/pocs/c1-permission-matcher.py))
- **Rule-authoring recipes (all byte-confirmed):** put broad allows in `allow`, carve-outs
  in `deny` (`"Bash"` in allow + `"Bash(rm -rf *)"` in deny works — deny is checked first);
  file writes must be `Edit(path)` rules, reads `Read(path)` rules; `Bash(git *)` covers
  bare `git`; never use `Write(path)`/`NotebookEdit(path)`/`MultiEdit(path)`/`Glob(path)`
  with a path — the validator PoC flags them.
- **Fleet security rule:** repo-controllable sources (project/local `.claude/settings.json`)
  can never grant `bypassPermissions` or `auto` — but verify the admin kill-switch
  `permissions.disableBypassPermissionsMode: "disable"` in managed settings for defense in depth.
- **MCP rule syntax:** allow patterns need a literal `mcp__<server>__` prefix with the glob
  only in the tool position (`mcp__puppeteer__*`); deny/ask accept wildcards anywhere
  (`mcp__*`). Plugin-bundled servers are named `mcp__plugin_<plugin>_<server>__<tool>`.
