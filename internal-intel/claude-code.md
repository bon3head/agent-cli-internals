# Internal intel — Claude Code CLI (2.1.287)

**CONFIRMED** = byte-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

## Model families: public vs internal-only (CONFIRMED)

> **Landscape correction (2026-10-18):** Fable 5/5.1 were framed here as unreleased — wrong.
> Fable 5 launched publicly 2026-06-09, Fable 5.1 on 2026-09-01 ($10/$50 per MTok).
> **Mythos 5/5.1 is the genuinely non-public family** (Project Glasswing restricted).

Two embedded catalogs: a signed compiled seed (v1468, issued 2026-10-01, key `claude-code-release-signing-key`, offset 215173117; surfaces cc/ccd/ccr/chat/cowork) and a richer 21-model internal registry (offset 199521935).

- **Fable 5 / 5.1** — PUBLIC flagship: `best:"fable"` in aliases, Jan/Jun 2026 cutoffs, `$10/$50` tier, capability flags (`fable_5_mitigations`, `adaptive_thinking`, `fast_mode`), `advisor_rank` 9 (top), effort nudges via `radiant_island`/`steady_plum`.
- **Mythos 5 / 5.1** — internal-only: every third-party provider_id null, first_party only, no alias, no fallback.
- Also in this build (public status of these versions UNVERIFIED, not claimed as unreleased): opus-4-6/4-7/4-8, sonnet-4-6, opus-5/5-5, sonnet-5/5-5. `opus-4-5-20251101` sits in `section:"deprecated"`.
- Internal pricing codes (`tier_10_50_cache_read_0_25`…), per-effort cost multipliers (`effort_cost_index`: sonnet-5 max = 5.59x).
- **Per-provider alias skew**: foundry's "opus" = 4-6, gateway's = 4-7 — third-party lags first-party ~1 minor version.
- Served catalog: `downloads.claude.ai/model-catalog/v1/catalog.json` + SPKI-verified `.raw-sig.json`. The in-binary compiled seed **expired 2026-10-08** — the live served catalog is what matters.
- Version gates: `min_claude_code_version` per model (e.g. 2.1.280 for opus-5-5), org-policy min-version floor, per-model `disabled` kill-switch, `minimumVersion` anti-downgrade pin.
- `autoUpdatesChannel` ∈ {latest, stable, rc} ("rc" displayed as "slow").
- Defaults: cc surface = claude-opus-5 (NOT 5-5); chat/cowork = claude-sonnet-4-6 (trails the CLI surface).
- Voice pipeline backends: only opus-5/sonnet-5 (Fable voice routes to Opus 5).

## Experiment gates (CONFIRMED)

549 distinct `tengu_*` gate names on re-enumeration (prior "128" count withdrawn as filter-dependent), evaluated through **GrowthBook** (not Statsig) — remoteEval against `https://api.anthropic.com/` with embedded SDK client key. Grounded examples: `pewter_owl_model` (remote model-routing override; env `CLAUDE_CODE_PEWTER_OWL`), `curious_tower_stateless_models` (stateless-model allowlist), `saffron_*` (billing), `smooth_harbor` (extra-usage billing), `kairos_cron` (scheduling; killable via `CLAUDE_CODE_DISABLE_CRON`), `harbor_kite_cloud` (cloud sessions; needs `CLAUDE_CODE_HARBOR_KITE_CLOUD`). Family codenames: `kairos`=scheduling, `harbor`=cloud+billing, `fleetview`=background-agent roster, `violin`=cloud remote-tools, `grove`=policy/privacy UI, `cobalt`=artifacts (HIPAA/ZDR-gated), `lantern`=session wrap-up.

## Product URLs and staging (CONFIRMED)

`anthropic.com/news/claude-fable-5-mythos-5` · `anthropic.com/claude/fable` (unreleased at build time; now live public announcements). Staging: `api-staging.anthropic.com`, `claude-ai.staging.ant.dev`, `claude-staging.fedstart.com`. 63 `code.claude.com/docs` paths inventoried (incl. `/docs/en/fast-mode`, `/docs/en/auto-mode-classifier-billing`).

## KILLS

- **`recommendedPlugins`**: 0 hits in all case variants — absent in 2.1.287.
- **Plugin sharing**: 0 hits — absent.
- **Embedded changelog**: runtime-fetched from GitHub raw, not embedded (not fetched per no-network constraint).
- **"Experimental"/"Internal" labels**: just /config UI tabs, not hidden features.
- **TODO comments**: vendored scaffold noise, not roadmap.
- **Chunk-manifest u32 semantics**: 5 hypotheses dead (size, blob offset, section-relative offset, name-string offset, length-prefix walk) — likely a runtime registry key.
- **Partial-clone upload for ultrareview**: no strings; upload is the branch diff (staged+unstaged, not untracked).
- **`chronicle` purpose**: flag exists, zero functional strings (carried from the codex pass).

## INFERENCE (gaps named)

- Fable voice routing rule (only backends observed, no routing rule byte-confirmed).
- Third-party alias lag as deliberate availability policy (pattern across 4 providers, no policy string).
- Pricing codes as $X/$Y per MTok (format consistent, no dollar mapping string).
- `ccd`/`ccr` surface semantics (appear in seed surfaces + `CLAUDE_CODE_ENTRYPOINT` values; role unverified).

## Prompt corpus (2026-10-20, CONFIRMED)

- **There is no stored main system prompt.** The preamble ships in three style variants (Proactive / Concise / Explanatory, offsets 98158416 / 98158740 / 98159024) and the rest is shared sections (Git Safety Protocol, PR creation, output style). The system prompt is assembled at runtime from fragments. Full corpus: [finding 17](../findings/claude-code/17-prompt-corpus.md), texts in [prompts/claude-code.md](../prompts/claude-code.md).
- **The served prompt is captured and compact (2026-10-20, local stub-endpoint capture, canned responses).** Each entrypoint serves 3 blocks: billing header, identity line, main agent block. sdk-cli: 6,117 chars, identity "You are a Claude agent, built on Anthropic's Claude Agent SDK." Interactive cli: 6,367 chars, identity "You are Claude Code, Anthropic's official CLI for Claude." The main block is not assembled from the stored preambles; it opens with the standalone string at offset 98182736. Identity lines sit at offsets 99654300 (cli) / 99654472 (sdk-cli). A separate system-role "# Environment" message (~20K chars) rides alongside. Most behavior text lives in tool descriptions and reminders, not the prompt. Texts: [prompts/claude-code.md](../prompts/claude-code.md) §0.
- **Tool descriptions recovered in full via the same capture**: 30 tools, full descriptions + input-schema JSON (Bash, Read, Edit, Write, Agent, CronCreate, Monitor, ...). Statically absent because served, not stored as text runs. Tool count varies by entrypoint/mode (24 headless, up to 42 interactive).
- **The security review agent prompt is complete in the binary** (10,709 chars): scope resolution, defect taxonomy, signal-to-noise bar. A reusable audit protocol, shipped as data.
- **Claude in Chrome is a separate prompted surface:** browser-automation instruction pack with its own tool namespace (`mcp__claude-in-chrome__*`).
- Built-in agent library in full: Plan, Explore, general-purpose, review-for-recall, review-for-precision, batch orchestrator, memory extraction/selection, workflow-script agents, agent teams.
