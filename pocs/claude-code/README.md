# PoCs — Claude Code CLI

All scripts are read-only against the analyst's own machine and auth. Trial status: re-run 2026-10-19.

| PoC | What it does | Trial outcome |
|---|---|---|
| `auth-surface-audit.py` | Read-only audit of local credential storage layout (paths, modes, key names, env-set; never values) | CONFIRMED live — exit 0 |
| `c1-permission-matcher.py` | Permission-rule parser/validator + decision simulator (deny > ask > allow > passthrough) | CONFIRMED live — ALL PASS |
| `c1-settings-validator.py` | Validates settings.json against the recovered 199-key schema (warns on the Write(path) gotcha) | CONFIRMED live — 0 errors on clean fixture, 1 error + warnings on bad fixture, 0 errors on live ~/.claude/settings.json |
| `cloud_mapper.py` | Binary → 8-table cloud/gateway reference (endpoints, flags, env vars, id regexes) | CONFIRMED live — 291 values on live binary |
| `extract_mcp_plane.py` (+ `verify_poc.py`) | MCP endpoint/marketplace inventory → JSON + markdown | CONFIRMED live — red-green verified, 35 ground-truth items PASS |
| `extract_model_catalog.py` | Served-seed + 21-model registry extraction → JSON + markdown table | CONFIRMED live — reusable for diffing future builds |

Usage: `python3 <poc>.py` — see each script's header. No credential values are ever printed. No network calls.
