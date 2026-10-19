# 08 — Embedded docs ARE the runtime skill corpus (10/12 byte-identical on disk)

**Trial status:** CONFIRMED at suite level (17/17 on the same binary). Trial spot-check counted the on-disk corpus present (`~/.gemini/antigravity-cli/builtin/skills/`: 9 skill dirs, 19 `.md` files); the 10/12 byte-identity claim was not re-diffed in the trial ("out of scope") — it stands on lane A2's verified carves.

---

## 1. WHAT WAS FOUND

All 12 embedded customization docs were carved from the binary with exact rodata offsets (52,408 bytes total); **10 of 12 are byte-identical** to the copies materialized on disk at `~/.gemini/antigravity-cli/builtin/skills/`. The binary's rodata IS the skill corpus the CLI mounts. Byte-exact carves (CONFIRMED):

| Doc | Offset range | Size | vs disk |
|---|---|---|---|
| `agy-customizations/SKILL.md` | 94183077 → 94188542 | 5,465 | byte-identical |
| `docs/rules.md` | 93070574 → 93072331 | 1,757 | byte-identical |
| `docs/skills.md` | 93321441 → 93324091 | 2,650 | byte-identical |
| `docs/plugins.md` | 93846442 → 93850789 | 4,347 | byte-identical |
| `docs/hooks.md` | 95255018 → 95268147 | 13,129 | byte-identical |
| `docs/mcp_servers.md` | 93516168 → 93519546 | 3,378 | byte-identical |
| `docs/json_configs.md` | 94017651 → 94022555 | 4,904 | byte-identical |
| `antigravity_guide/SKILL.md` | 93426046 → 93429069 | 3,023 | byte-identical |
| `references/cli.md` | 93044894 → 93048272 | 3,378 | **DIVERGES**: binary copy has a 13-line sed-tool block (lines 42–54) the disk copy lacks — binary is the newer/superset copy |
| `references/ide.md` | 93522931 → 93526330 | 3,399 | byte-identical |
| `references/app.md` | 93666982 → 93670834 | 3,852 | byte-identical |
| `references/sdk.md` | 93441408 → 93444534 | 3,126 | **DIVERGES**: binary copy is missing the closing fence — truncated by one line (cosmetic) |

The carve also fully documents the customization system: 5 types (rules / skills / plugins / hooks / MCP servers), discovery roots (workspace `.agents/` walking CWD→repo root, global `~/.gemini/config/`), load precedence, progressive disclosure (skills inject name+description only), budgets (24KB/file, 20k-token rules budget), and the Python SDK (`pip install google-antigravity`; `Agent` + `LocalAgentConfig` + `CapabilitiesConfig`; repo `github.com/google-antigravity/antigravity-sdk-python`).

On-disk layout mapped: `settings.json`, `installation_id`, `antigravity-oauth-token` (0600), `jetski_state.pbtxt`, `brain/<uuid>/`, `conversations/<uuid>.db`, `conversation_summaries.db`, `builtin/skills/` (9 skills + `keep.txt`), `bin/agentapi`, `log/`, `updater/`. Absent here: `workflows.json`/`global_workflows/` (legacy system fully migrated away), `jetski/`, `sidecar.json`.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A2 (config schema). Marker-anchored carve technique (strings interleaved with chroma lexer XML + proto descriptors defeated naive offset carving; walk-back/forward over-grabbed; marker-anchored carve + content-based end trim produced 12 clean carves). Eureka ~22:10: `~/.gemini/antigravity-cli/builtin/skills/` exists on disk; diff of all 12 carves vs disk → 10/12 byte-identical.

---

## 3. WHAT IT UNLOCKS

The skills and guides the agent reads at runtime are not downloaded from anywhere — they are baked into the program itself, and ten of twelve survive the trip from inside the binary to the files on your disk byte-for-byte. That means the documentation is version-locked to the exact binary you run: the rules you see are the rules the agent was built with. And where the two copies differ, the binary is the newer one — it already knows a sed-based editing tool the on-disk copy never got.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Author skills with the embedded schema:** `skills/<name>/SKILL.md` with required frontmatter `name` (lowercase-hyphenated, unique) + `description` (third-person, what + when — the agent reads this to decide activation). Optional `scripts/`, `examples/`, `resources/`, `references/`.
- **Rules:** `GEMINI.md`/`AGENTS.md` at project root (no frontmatter, always active for directory scope); hard budgets 24,000 bytes/file, 20,000-token aggregate rules budget.
- **Plugins:** `plugins/<name>/plugin.json` + enable-state in `config.json` → `{plugins: {"<dir-name>": {enabled: true|false}}}`. `agy plugin install|enable|disable`.
- **MCP servers:** `~/.gemini/config/mcp_config.json` → `{mcpServers: {"<id>": {command, args?, env?} | {url}}}`. Legacy HTTP+SSE unsupported — use a stdio bridge like `mcp-remote` for SSE-only servers.
- **Explicit registration:** `skills.json` / `plugins.json` with `{entries: [{path, include_only?, exclude?}], inherits: [{path, include_only?, exclude?}]}` for customizations outside default discovery roots.
- **Diff binary vs disk after updates:** re-carve at the offsets above and diff against `builtin/skills/` — divergences (like the cli.md sed-tool block) are advance notice of features the shipped docs haven't caught up to.
