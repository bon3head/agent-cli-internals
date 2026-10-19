# PoCs — Antigravity CLI

All scripts are read-only against the analyst's own machine and auth. Trial status: re-run 2026-10-19, all exit 0.

| PoC | What it does | Trial outcome |
|---|---|---|
| `a1_enumerate_surfaces.py` | Binary path → full local surface inventory: gRPC method census by service, 43 real `ANTIGRAVITY_*` env vars, listener/socket indicators, evidence offsets | CONFIRMED live — 603-line inventory, sha256 match |
| `a1_probe_health.py` | Single-shot read-only `GET /healthz` against localhost:5387, 2s timeout, no retry | CONFIRMED live — connection refused (no LS running on this box, as designed) |
| `a3_token_inspector.py` | Parses the user's own oauth-token file; prints ONLY structure/expiry/key shapes, zero secret bytes | CONFIRMED live — token structure read, file mode 0600 |
| `a6_pclntab_dump.py` | Parses Go pclntab → full function inventory TSV, 2.9s, <100MB RAM | CONFIRMED live — exactly 164,366 + 19,312 (cgo) functions |

Usage: `python3 <poc>.py` — see each script's header for arguments. No network calls beyond the localhost health probe. No secrets are printed by any script.
