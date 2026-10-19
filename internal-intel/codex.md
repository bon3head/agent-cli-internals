# Internal intel — Codex CLI (0.155.1; schema/flag baseline 0.149.0)

**CONFIRMED** = byte-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

## Roadmap signals (CONFIRMED)

- **`guardian_subagent`** is an `ApprovalsReviewer` enum seat: `"user" | "auto_review" | "guardian_subagent"` — an AI that approves/denies tool calls instead of the user. The autonomy unlock. Related: `guardianv2` watches transcripts (`tool_calls`, `tool_outputs`, `reasoning`).
- **Realtime voice is coming**: full WebRTC module (`core/src/realtime_conversation.rs`, `offer_sdp` in `RealtimeConversationStart`), TUI `/voice` behind `/experimental`, API-key-auth only, 19-voice enum in two generations (v1/v2 served side by side).
- **Agent identity is coming**: `use_agent_identity` (under dev); strings `agent identity bootstrap unavailable; using ChatGPT bearer <redacted> for this session`, `failed to decode agent identity JWKS`. JWKS-based agent identities distinct from user tokens.
- **Token budgets are enforced, not advisory**: SQLite trigger `WHEN ? = 'active' AND token_budget IS NOT NULL AND tokens_used >= token_budget THEN ?` fires auto-compaction. Separate `rollout_budget` metering in "rollout budget units" with reminder thresholds.
- **Multi-agent v2**: parallel threads per session (`max_concurrent_threads_per_session`), disabled by default.
- **Memories = distillation pipeline**, not vector store: `raw_memories.md` (ingestion queue) → `rollout_summaries/*.md` → `# Task Group` MEMORY blocks; `memories_v2_1.sqlite`. Stable but off by default.
- **Model ladder**: Luna = speed/cost, Terra = balanced, Sol = ? (unresolved). GPT-5.4 is **already retired in-binary** ("GPT-5.4 is no longer available\n\nCodex now uses GPT-5.6 Terra in place of GPT-5.4. Switch to GPT-5.6 Terra to continue."). GPT-6 Astra has embedded migration guides and prompting best-practices; an anti-hallucination guardrail literally says: `do not invent a separate gpt-6-pro model slug`.
- **`code_mode_only`**: latent `tool_mode` enum value that would force ALL model tool use through V8 cells.
- **Bedrock is first-class**: setup wizard, `x-amzn-mantle-client-agent` header, `codex-bedrock-credential-export` catalog token, `AWS_BEARER_TOKEN_BEDROCK`. EU/FedRAMP residency is a control plane (`x-openai-internal-codex-residency`, `chatgpt_account_is_fedramp`).
- **Hosted services compiled in**: `https://serpi.openai.com/v1` (SERP-as-MCP), `https://persistent.oaistatic.com/codex/pets/v1` (TUI pets assets).

## Consolidation direction (CONFIRMED)

Websockets transport removed · legacy sandboxes (landlock/bwrap) removed/deprecated · old web-search flags deprecated in favor of provider-capability search · `tui_app_server` removed (replaced by the current app-server protocol). The `[EXPERIMENTAL]` tag on `codex cloud` is a support-policy marker, not a stub — all five subcommands are present and working.

## Codenames / family branding (CONFIRMED)

Astra · Terra · Luna · Sol are a celestial-body family naming scheme, not one-offs. `sol` doubles as a model codename AND a voice name — family branding leaks across surfaces.

## Internal endpoints (CONFIRMED)

`https://api.chatgpt-staging.com` · `go/codex-feedback/` · `go/codex-feedback-internal` · `go/codex-employee-feedback-faq` · build provenance GitHub Actions (`/home/runner/work/codex/codex`), monorepo `codex-rs`.

## KILLS

- **`chronicle` purpose**: flag exists, zero functional strings — dead.
- **`https://chatgpt.com/oauth/codex/client.json` as a login endpoint**: surrounding strings prove it belongs to MCP OAuth client registration, not login.
- **`OTEL_SDK_DISABLED` works as a kill switch**: zero hits in the binary — it silently does nothing.
- **`client_id` recoverable from the binary**: self-redacting format strings; scrubbed at compile time.

## INFERENCE (gaps named)

- Agent identity timeline (strings confirm the feature; ship date unverified).
- `gpt-6-astra` is a PUBLIC model (launched 2026-09-03, API id `gpt-6-astra`, $10/$50 per MTok) — listed in the 0.155.1 catalog; the open question is CLI servability per plan tier, not existence. Note: the astra slug is a **0.155.1-era addition** — absent from 0.149.0 binary strings and its live catalog; the REA schema/flag baselines were captured against 0.149.0.
