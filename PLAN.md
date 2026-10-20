# Repo build plan — agent-cli-internals

## Findings inventory (34 finding docs + 3 intel docs)

**Antigravity CLI** (`findings/antigravity/`, 12): 01-local-control-plane (341-method LS, localhost:5387) · 02-safety-screen (per-step 2-stage) · 03-model-catalog (server-driven, alias map) · 04-auth (code-assist machinery) · 05-telemetry (3 pipelines, no CLI kill switch) · 06-sidecar-server (token-authed HTTP) · 07-hook-contract · 08-embedded-skill-corpus · 09-pclntab (164k functions) · 10-remote-mesh · 11-internal-intel-overview · 12-byo-model-path (AGY_LLM_GATEWAY_*)
**Claude Code CLI** (`findings/claude-code/`, 12): 01-bundle-surgery (41MB carve) · 02-settings-schema (199 keys) · 03-permission-engine · 04-hook-events (33) · 05-cloud-control-plane · 06-gateway-server · 07-mcp-plane · 08-plugin-plane · 09-auth-plane · 10-fable-mythos · 11-experiment-gates · 12-hidden-flags
**Codex CLI** (`findings/codex/`, 10): 01-app-server-protocol · 02-wire-quirks · 03-transports · 04-code-mode-host · 05-config-surface · 06-auth · 07-rate-limits · 08-telemetry · 09-mcp · 10-codex-cloud
**Internal intel** (`internal-intel/`): antigravity.md (codenames, kill switches, lineage) · claude-code.md (Fable/Mythos, tengu gates, staging) · codex.md (guardian_subagent, realtime voice, agent identity…)

**2026-10-20 fold-in:** prompt corpora for all four tools (agy 16, claude 17, codex 14 finding docs; new `findings/muse/` with 01) + codex gated-rerun doc (15) · verbatim prompt texts in `prompts/` · `internal-intel/muse.md` added · dated corrections in place in codex findings 05, 06, 08, 13.

## Repo structure

```
agent-cli-internals/
  README.md                      — layman "what this unlocks" + findings index ranked by bigness
  findings/antigravity/*.md      — 12 docs, 4 sections each
  findings/claude-code/*.md      — 12 docs, 4 sections each
  findings/codex/*.md            — 10 docs, 4 sections each
  internal-intel/{antigravity,claude-code,codex}.md
  methodology/README.md          — techniques per target + tool-call inventory
  diagrams/*.mmd                 — mermaid: agy LS topology, claude cloud attach, codex protocol flow,
                                   telemetry pipelines (3), permission decision flow, agent trajectory
  pocs/{antigravity,claude-code,codex}/ — all durable PoCs + per-PoC README with trial outcome
  eureka-log.md                  — chronological eurekas + full scratchpads
```

Per-finding doc template: 1. WHAT WAS FOUND · 2. HOW IT WAS FOUND (agent/swarm, log excerpts, exact commands) · 3. WHAT IT UNLOCKS (layman) · 4. HOW A DEVELOPER BUILDS ON IT.

## Trial scorecard (Phase 1)

Re-run every PoC / live read-only verification; record CONFIRMED live / PARTIAL / UNVERIFIABLE with exact command + output. Failed trials stay in repo marked as such. No secrets in outputs (a3 token inspector already metadata-only — verify). No metered-model quota burn. No destructive writes.

## Publish risks (Phase 3)

- **GitHub BLOCKED**: `gh` installed but not logged in (`gh auth status` → not logged into any hosts). Remediation: Justin runs `gh auth login` (device flow) or provides a token. Repo will be built fully locally at ~/workspace/rea-repo-build/repo/ and left push-ready.
- **Discord RISKY**: kabi-discord-cli is read-oriented (guilds/channels/history/search, no send command visible); `discord status` errors with connection_error. The messaging skill may offer a send path — to be evaluated in Phase 3; if no send path, report blocker with options (target server/channel list).
- Outward comms authorized by Justin for exactly this; keep posts to summary + link + top-5 layman unlocks; no credential-adjacent content.

## Sequencing

Phase 0 (this plan) → Phase 1 trials (3 workers: agy/claude/codex) → Phase 2 build (5 workers: 3× findings, 1× README+methodology+eureka+intel, 1× diagrams) → coordinator assembles + verifies → Phase 3 publish (attempt; report blockers honestly).
