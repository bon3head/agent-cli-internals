# 02 — Settings schema fully recovered: 199 typed keys (C1)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C1 (settings/permissions) · **Trial status:** CONFIRMED live
(`pocs/c1-settings-validator.py` re-run: clean fixture 0 errors/0 warnings; bad fixture 1 error + 2
warnings; live `~/.claude/settings.json` 0 errors/0 warnings, file mode 660)
**Confidence:** CONFIRMED (byte-level). Zod type-code mapping (`o()`=string, `M()`=bool, …) is INFERENCE from
usage patterns.

---

## 1. WHAT WAS FOUND

The entire settings schema is built by `function Ia()` at binary offset **199028346** (69 KB),
returning 192 field definitions merged with 5 unit shapes (`autoMode`, `deepLink`, `voice`,
`briefView`, `screenReader`) — dumped verbatim to `ia-func.txt` / `ia-schema-parsed.txt`
(199 keys total, each with zod type + describe). Byte-level anchors:

- The assembled schema is **`u(shape).passthrough()`** (CONFIRMED: from the schema class,
  `An.whole(){return this.wholeSchema??=u(this.shapeOf(this.keys)).passthrough()}`) —
  **unknown keys are kept, never rejected.** Typos in settings.json silently sit there.
- Five sources, fixed low→high precedence (CONFIRMED: `Li=["userSettings","projectSettings",
  "localSettings","flagSettings","policySettings"]` @198690770, describe:
  `"Ordered low-to-high priority \u2014 later entries override earlier ones."`):
  1. `userSettings` → `~/.claude/settings.json`
  2. `projectSettings` → `.claude/settings.json`
  3. `localSettings` → `.claude/settings.local.json`
  4. `flagSettings` → `--settings` CLI flag (always on)
  5. `policySettings` → managed tier (always on)
- `--setting-sources` only toggles the first three: `Xo()` builds the enabled set as
  `new Set(cliValues) + "flagSettings" + "policySettings"`, so `--setting-sources=user`
  still loads `--settings` files and managed policy. `--restricted` additionally ignores user,
  project and local files ("managed settings and --settings still apply").
- Managed tier order (CONFIRMED string): `"server-managed > MDM (managed plist / HKLM) >
  managed-settings.json"`. Linux: `/etc/claude-code/managed-settings.json`. A `policyHelper`
  executable can compute managed settings at startup ("Honored only from admin-controlled policy
  sources"). Managed-tier keys enforce: `permissions.disableBypassPermissionsMode: "disable"`,
  `allowManagedPermissionRulesOnly` (other rules listed with `notInEffect: true` and ignored),
  `allowManagedHooksOnly`, `allowManagedMcpServersOnly`, `strictKnownMarketplaces`.
- Invalid file handling (CONFIRMED strings): `"…could not be parsed as a JSON object; none of
  its settings are in effect. Fix or remove it."`; non-interactive (`-p`) mode silently ignores
  failing files ("no error dialog is shown").
- Project trust gate (CONFIRMED): `~/.claude.json → projects["<encoded-cwd>"].hasTrustDialogAccepted`
  (`le().projects?.[e]?.hasTrustDialogAccepted===!0`).
- PoC: `pocs/c1-settings-validator.py` enforces the recovered schema — warns (never errors) on
  unknown keys, and specifically warns on the `Write(path)` permission gotcha.

## 2. HOW IT WAS FOUND

- Lane C1: string-table extraction + targeted offset reads in the 0xcc80000–0xce00000 settings
  window; the 69 KB `Ia()` function was dumped in full from offset 199028346 (saved to
  `ia-func.txt`) and parsed key-by-key into `ia-schema-parsed.txt` (see
  `~/workspace/rea-claude/deep-dive/`).
- Source-list anchor `Li=[...]` found at 198690770; CLI-name map
  `u={userSettings:"user",projectSettings:"project",localSettings:"local"}` and the toggle set
  `Th=["userSettings","projectSettings","localSettings"]` at 198692371.
- The `.passthrough()` discovery was made inside the schema class method (`An.whole()`) — this
  explains the byte-level behavior that unknown keys never error.
- Trial (2026-10-18): `python3 c1-settings-validator.py clean.json bad.json ~/.claude/settings.json` →
  clean: `0 error(s), 0 warning(s)`; bad: `1 error(s), 2 warning(s)`
  (`model: expected str, got int`; warns on `Write(/tmp/x)` gotcha + unknown key); live
  `~/.claude/settings.json`: `0 error(s), 0 warning(s)`, mode 660. All match the REPORT's
  expected behavior; exit codes 0/1/2 documented.

## 3. WHAT IT UNLOCKS

In plain terms: you can now write a Claude Code settings file by hand and have it validated by
a real schema instead of trial-and-error — and you know exactly which file wins when several
say different things, and which knobs are admin-only. The "my settings change did nothing"
class of bugs (typos kept silently, `--setting-sources` not disabling `--settings`, project
settings silently ignored in `-p` mode) is now diagnosable offline.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Validate before deploy:** `python3 pocs/c1-settings-validator.py settings.json` — run it
  against any hand-written settings.json in CI or before shipping machine images; exit 1 means a
  real type error, warnings mean a typo or a gotcha.
  ([pocs/c1-settings-validator.py](sandbox://workspace/rea-claude/deep-dive/pocs/c1-settings-validator.py))
- **Precedence rules to hard-code:** merge order user → project → local → `--settings` →
  managed; `--setting-sources` never disables `--settings` or managed policy; `true` in
  `blockReadsOutsideWorkingDirectories` in *any* source wins (OR-semantics).
- **The 199-key reference:** `ia-schema-parsed.txt` is the complete key list with types +
  describes — generate IDE autocompletion / docs from it rather than re-extracting.
  ([ia-schema-parsed.txt](sandbox://workspace/rea-claude/deep-dive/ia-schema-parsed.txt))
- **Managed lockdown recipe:** ship `/etc/claude-code/managed-settings.json` with
  `disableBypassPermissionsMode: "disable"`, `allowManagedPermissionRulesOnly: true`,
  `allowManagedHooksOnly: true` — fleet admins can lock an entire estate from three lines.
