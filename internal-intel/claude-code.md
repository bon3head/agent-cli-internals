# Internal intel — Claude Code CLI (2.1.287)

**CONFIRMED** = byte-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

## Unreleased model families (CONFIRMED)

Two embedded catalogs: a signed compiled seed (v1468, issued 2026-10-01, key `claude-code-release-signing-key`, offset 215173117; surfaces cc/ccd/ccr/chat/cowork) and a richer 21-model internal registry (offset 199521935).

- **Fable 5 / 5.1** — flagship: `best:"fable"` in aliases, Jan/Jun 2026 cutoffs, `$10/$50` tier, capability flags (`fable_5_mitigations`, `adaptive_thinking`, `fast_mode`), `advisor_rank` 9 (top), effort nudges via `radiant_island`/`steady_plum`.
- **Mythos 5 / 5.1** — internal-only: every third-party provider_id null, first_party only, no alias, no fallback.
- Also unreleased in this build: opus-4-6/4-7/4-8, sonnet-4-6, opus-5/5-5, sonnet-5/5-5. `opus-4-5-20251101` sits in `section:"deprecated"`.
- Internal pricing codes (`tier_10_50_cache_read_0_25`…), per-effort cost multipliers (`effort_cost_index`: sonnet-5 max = 5.59x).
- **Per-provider alias skew**: foundry's "opus" = 4-6, gateway's = 4-7 — third-party lags first-party ~1 minor version.
- Served catalog: `downloads.claude.ai/model-catalog/v1/catalog.json` + SPKI-verified `.raw-sig.json`. The in-binary compiled seed **expired 2026-10-08** — the live served catalog is what matters.
- Version gates: `min_claude_code_version` per model (e.g. 2.1.280 for opus-5-5), org-policy min-version floor, per-model `disabled` kill-switch, `minimumVersion` anti-downgrade pin.
- `autoUpdatesChannel` ∈ {latest, stable, rc} ("rc" displayed as "slow").
- Defaults: cc surface = claude-opus-5 (NOT 5-5); chat/cowork = claude-sonnet-4-6 (trails the CLI surface).
- Voice pipeline backends: only opus-5/sonnet-5 (Fable voice routes to Opus 5).

## Experiment gates (CONFIRMED)

128 `tengu_<adjective>_<noun>` gates, server-driven via `featureGateLookup` with compiled local defaults. Grounded examples: `pewter_owl_model` (remote model-routing override; env `CLAUDE_CODE_PEWTER_OWL`), `curious_tower_stateless_models` (stateless-model allowlist), `saffron_*` (billing), `smooth_harbor` (extra-usage billing), `kairos_cron` (scheduling; killable via `CLAUDE_CODE_DISABLE_CRON`), `harbor_kite_cloud` (cloud sessions; needs `CLAUDE_CODE_HARBOR_KITE_CLOUD`). Family codenames: `kairos`=scheduling, `harbor`=cloud+billing, `fleetview`=background-agent roster, `violin`=cloud remote-tools, `grove`=policy/privacy UI, `cobalt`=artifacts (HIPAA/ZDR-gated), `lantern`=session wrap-up.

## Unreleased-product URLs and staging (CONFIRMED)

`anthropic.com/news/claude-fable-5-mythos-5` · `anthropic.com/claude/fable`. Staging: `api-staging.anthropic.com`, `claude-ai.staging.ant.dev`, `claude-staging.fedstart.com`. 63 `code.claude.com/docs` paths inventoried (incl. `/docs/en/fast-mode`, `/docs/en/auto-mode-classifier-billing`).

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
