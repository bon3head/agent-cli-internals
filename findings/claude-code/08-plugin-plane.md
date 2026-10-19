# 08 — Plugin plane: marketplace = GCS + git, sha256-pinned trust (C3)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C3 (MCP/plugins) · **Trial status:** CONFIRMED live (`claude --help` lists
`plugin|plugins  Manage Claude Code plugins`; `pocs/verify_poc.py` → `PASS: all 35 ground-truth
items present; kills hold`)
**Confidence:** CONFIRMED (byte-level). Full plugin.json JSON schema (required vs optional fields)
unrecovered — only the `manifest.<field>` reference set. Plugin distribution is described as INFERENCE
("the distribution vehicle for skills+agents+hooks+MCP servers") from the trust machinery.

---

## 1. WHAT WAS FOUND

- `claude plugin` subcommands (live `--help`): `configure`, `details` (component inventory +
  **projected token cost**), `disable`/`enable`, `eval`, `init|new`, `install|i`, `list`,
  `marketplace`, `prune|autoremove`, `tag` (`{name}--v{version}` git tag, validates plugin.json ↔
  marketplace entry version agreement), `test`, `uninstall|remove`, `update`, `validate`.
- Plugin identity: `name@source`. Sources (CONFIRMED): **marketplace** (`plugin@marketplace`),
  **`skills-dir`** (`plugin init` scaffolds `~/.claude/skills/<name>/`, auto-loads as
  `<name>@skills-dir`), **`builtin`** ("this Claude Code bundles a plugin of that name"),
  **`claudeai`** (synced from claude.ai catalog), **npm** (`<package>@npm` — account-gated:
  `"Installing plugins straight from an npm registry (`<package>@npm`) is not enabled for this
  account."`).
- Marketplace protocol (CONFIRMED): add sources by URL, local path, or GitHub repo; marketplace
  kinds: git repo / git remote / hosted `marketplace.json` / npm package containing
  `marketplace.json`; **fetch = GCS primary, git fallback**
  (`"marketplace GCS failed; falling back to git"`); default
  `plugin_marketplaces: 'https://github.com/anthropics/claude-code.git'`.
- **Trust model:** `installationPreference` ∈ `available | required | auto_install | not_available`.
  `required`/`auto_install` enforce **only with a `manifestSha256` pin** (or full 40-char commit
  SHA in `ref`); without it they degrade to `available`. Marketplace-declared commands
  (command-source installs, `headersHelper` archive fetches) are shown in a consent UI and must
  be accepted; `--accept-command <sha256>` accepts exactly that command for that plugin+catalog;
  a catalog refresh that changes the command **refuses and re-prompts**. `"a plugin the user
  removes stays removed until the pin changes"`.
- Plugin bundle anatomy: manifest `.claude-plugin/plugin.json` (`name`, `version`,
  `description`, `author`, `license`, `homepage`, `repository`, `userConfig`, `hooks`,
  `mcpServers`, `lspServers`, `outputStyles`, `channels`, `monitors`, `workflows`, `strict`).
  Component dirs: `commands/`, `agents/`, `skills/` (+ `SKILL.md`), `hooks/`,
  `output-styles/`, `monitors/`, `workflows/`, `.mcp.json`, `.lsp.json`. `${CLAUDE_PLUGIN_ROOT}`
  env var available to plugin scripts.
- **userConfig:** manifest-declared schema; sensitive values go to secure storage (keychain),
  non-sensitive stored as options; settable via `plugin configure` / `install --config
  key=value`.
- **Bundled MCP servers:** `.mcpb` (29 hits) and `.dxt` (Desktop Extension) bundle files;
  `.mcpb-cache` extraction dir; plugin-root `.mcp.json` may point `mcpServers` entries at
  `.mcpb` files.
- **`plugin eval`:** `evals/**/case.yaml` (or `prompt.md` + `graders/*.md`); runs on your
  machine **as you**; "sandboxing limits what a malicious plugin can reach but is not a
  guarantee"; `--trust-plugin` for CI; includes a no-plugin baseline arm.
- Admin control: `strictKnownMarketplaces` / `blockedMarketplaces` under managed settings —
  end-to-end admin gating of plugin sources.
- **KILLS (0 hits, all case variants):** `recommendedPlugins` does not exist in 2.1.287;
  plugin sharing (`plugin share` / `sharePlugin`) does not exist; `claude mcp
  enable/disable` does not exist (enable/disable is plugins-only).

## 2. HOW IT WAS FOUND

- Lane C3: string-table scans + `claude plugin --help` introspection; marketplace fetch path
  found via the `"marketplace GCS failed; falling back to git"` string; trust model from the
  `manifestSha256` / `installationPreference` / `--accept-command <sha256>` string cluster;
  bundle anatomy from the `.claude-plugin/plugin.json` manifest field references.
- PoC: `pocs/extract_mcp_plane.py` includes the marketplace inventory in its JSON+MD output.
- Kill verification: zero-hit searches across all case variants for `recommendedPlugins`,
  `recommended-plugins`, `recommended_plugins`, `plugin share`, `sharePlugin`, `pluginShare`.
- Trial (2026-10-18): `verify_poc.py` → `PASS: all 35 ground-truth items present; kills hold.`

## 3. WHAT IT UNLOCKS

In plain terms: plugins are how you package bespoke tooling — a skill, a slash command, a hook
set, and an MCP server — into one versioned, installable, sha256-pinned bundle. The trust
model (pins, per-command consent, admin allowlists) means you can ship tooling to a whole team
or company without handing them a bag of unsigned scripts.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Packaging recipe:** `claude plugin init` scaffolds `~/.claude/skills/<name>/`
  (auto-loads as `<name>@skills-dir`); add `commands/`, `agents/`, `hooks/`,
  `output-styles/`, `.mcp.json`; declare user-facing config in `userConfig` (secrets land in
  secure storage automatically); ship `.mcpb`/`.dxt` bundles for bundled servers.
- **Distribution:** publish a marketplace (git repo or npm package containing
  `.claude-plugin/marketplace.json` with `plugins[] = {name, path, source?, version?}`);
  fetch is GCS-first, git fallback; pin every install with `manifestSha256` (or 40-char
  commit SHA in `ref`) or `required`/`auto_install` silently degrades to `available`.
- **Security posture:** marketplace commands and `headersHelper` fetchers require consent UI
  + `--accept-command <sha256>`; catalog changes to a command refuse and re-prompt.
  Enterprise: `strictKnownMarketplaces` / `blockedMarketplaces` in managed settings;
  `disableCommandPluginSources: true` kills command-sourced plugin installs fleet-wide.
- **Quality gate:** `claude plugin eval` with `evals/**/case.yaml` + graders, with the
  built-in no-plugin baseline arm; `plugin details` shows projected token cost before install.
