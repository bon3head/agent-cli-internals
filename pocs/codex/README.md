# PoCs — Codex CLI

This target had no standalone PoC scripts; its "trials" were live read-only extractions, all re-run 2026-10-19 with 8/8 CONFIRMED:

| Trial | Command | Outcome |
|---|---|---|
| Protocol schema extraction | `codex app-server generate-json-schema --out <dir>` | CONFIRMED — 291 schema files, byte-identical to repo baseline |
| Feature flag inventory | `codex features list` | CONFIRMED — 118 lines on v0.149.0, diff identical to `feature-flags.txt` |
| Wire-quirk check | parse re-generated `JSONRPCRequest.json` | CONFIRMED — required: `["id","method"]`, no `jsonrpc` property |
| Help surfaces | `codex --help`, `app-server --help`, `mcp --help`, `debug --help` | CONFIRMED — all render |
| Health | `codex doctor` (timeout 60) | CONFIRMED — exit 0, checks green |
| Auth file perms | `ls -la ~/.codex/auth.json` | CONFIRMED — mode 0600, metadata only |
| gpt-6-astra presence | strings grep on 0.155.1 binary + `codex debug models` | CONFIRMED on 0.155.1 (19 string hits; catalog lists gpt-6-astra/luna/sol); ABSENT on 0.149.0 |

Version pinning: PATH `codex` → v0.149.0 (`/opt/hatch-image/bin/codex`); REA-analyzed binary is 0.155.1 at `~/.bun/install/global/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex`. Claims in `findings/codex/` state which version they were verified against.
