# 10 — Model families in the binary: Fable 5/5.1 (public) and Mythos 5/5.1 (internal-only) (C5)

> **Landscape correction (2026-10-18):** an earlier revision of this doc framed Fable 5/5.1 as
> unreleased. That was wrong. **Fable 5 launched publicly June 9, 2026; Fable 5.1 launched
> publicly September 1, 2026** (both $10/$50 per MTok). The genuinely non-public family is
> **Mythos 5/5.1** — see below.

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C5 (internal intel) · **Trial status:** CONFIRMED live (`pocs/extract_model_catalog.py`
re-run → exit 0: `seed: version=1468 issued=2026-10-01T08:56:01Z expires=2026-10-08T08:56:01Z
key=claude-code-release-signing-key surfaces=['cc','ccd','ccr','chat','cowork']` /
`registry: 21 models, aliases=['opus','sonnet','haiku','fable']`; byte anchors @215173117 and
@199521935 re-read live → byte-exact)
**Confidence:** CONFIRMED (byte-level). Dollar mapping of pricing codes, Fable voice routing,
`ccd`/`ccr` surface semantics, and third-party lag as deliberate policy are INFERENCE (gaps named).
**KILL:** `chronicle` — flag exists, zero functional strings (same as the codex pass).

---

## 1. WHAT WAS FOUND

Two embedded model catalogs:

- **Signed compiled seed** (v1468, issued 2026-10-01T08:56:01Z, expired 2026-10-08T08:56:01Z,
  key `claude-code-release-signing-key`) at binary offset **215173117** — anchor:
  `{$schema:"https://downloads.claude.ai/model-catalog/v1/schema.json",schema_version:1,
  version:1468,...`. Surfaces: `cc`, `ccd`, `ccr`, `chat`, `cowork`.
- **Richer internal registry** — 21 models — at offset **199521935**.

**Fable 5 / 5.1** — PUBLIC models (Fable 5 launched 2026-06-09; Fable 5.1 launched 2026-09-01;
$10/$50 per MTok). Cutoffs Jan 2026 / Jun 2026, pricing `tier_10_50` /
`tier_10_50_cache_read_0_25`, `best:"fable"` in the alias table — positioned as the flagship
tier **above Opus**. Fable is third-party-bound: full provider_ids,
`VERTEX_REGION_CLAUDE_FABLE_5[_1]` env vars, `fallback_3p: claude-opus-5-5`.

**Mythos 5 / 5.1** — the genuinely INTERNAL-ONLY family: every third-party provider_id is
null, first_party only, no alias, no fallback, no Mythos entry in `latest_per_family`
addressability — the `mythos` alias does not exist at all. Public reporting (June–Sept 2026)
says Mythos shares Fable's underlying weights with safeguards lifted and is restricted to
vetted cyberdefenders/infrastructure providers via Project Glasswing. The binary confirms
the posture independently: null 3p provider_ids are the footprint of a model the public is
not meant to address. Both families carry `fable_5_mitigations` capability flags
(internal safety mitigations bundle).

The registry also lists opus-4-6/4-7/4-8, sonnet-4-6, opus-5/5-5, sonnet-5/5-5 — public
status of these versions is UNVERIFIED from this binary alone (not claimed as unreleased);
`claude-opus-4-5-20251101` sits in `section:"deprecated"`.

Aliases (@199537503): `opus.default = claude-opus-5-5`, `sonnet.default = claude-sonnet-5-5`,
`fable.default = claude-fable-5-1`, `haiku.default = claude-haiku-4-5`,
`latest_per_family: {fable: claude-fable-5-1, opus: claude-opus-5-5, sonnet: claude-sonnet-5-5,
haiku: claude-haiku-4-5}`. **Per-provider alias skew**: foundry's "opus" = opus-4-6,
gateway's "opus" = opus-4-7; bedrock/vertex/foundry/mantle "sonnet" = sonnet-4-5 while
anthropic_aws/gateway = sonnet-4-6 (INFERENCE: third-party availability lags first-party
~1 minor version).

Internal levers: **pricing codes** (`tier_15_75`, `tier_5_25`, `tier_4_20_cache_read_0_20`,
`tier_3_15`, `tier_2_10`, `tier_10_50`, `tier_10_50_cache_read_0_25`, `haiku_35`, `haiku_45`
— INFERENCE: `$X/$Y` per MTok in/out), **`effort_cost_index`** per-effort cost multipliers
(sonnet-5 max = 5.59x; fable-5-1 `{0.75,0.86,1,1.38,1.74}`), **`advisor_rank`** (fable-5-1 = 9,
top; mythos-5-1 = 9), **capability flags** (`fable_5_mitigations`, `adaptive_thinking`,
`fast_mode`, `opus_5_prompt_bundle`, …).

Version gates: `min_claude_code_version` (opus-5-5 → `2.1.280`; fable-5-1 → `2.1.251`) —
the picker drops models the build is too old for; per-model `disabled` kill-switch (the
server-side model-removal field); `settings_vocabulary` int-encodes settings
(`effort_level:{high:3,low:1,max:5,medium:2,xhigh:4}`).

Seed/catalog mechanics: the served catalog is `downloads.claude.ai/model-catalog/v1/catalog.json`
+ `.raw-sig.json`, verified with an embedded SPKI key (`spkiBase64`); "primary: served list
replaces the compiled picker". Since the compiled seed is **expired 2026-10-08**, the live
served catalog is what matters. Selector defaults: cc/ccd/ccr default = `claude-opus-5`
(NOT 5-5); chat/cowork default = `claude-sonnet-4-6`.

Unreleased-at-build-time product URLs embedded in the binary (now live public announcements):
`anthropic.com/news/claude-fable-5-mythos-5`, `anthropic.com/claude/fable`. Staging hosts:
`api-staging.anthropic.com`, `claude-ai.staging.ant.dev`, `claude-staging.fedstart.com`.

PoC: `pocs/extract_model_catalog.py` → seed JSON, 21-model registry JSON, aliases JSON,
markdown table. Reusable for diffing future builds (watch `version`, `issued_at`, new ids).

## 2. HOW IT WAS FOUND

- Lane C5: the `{$schema:"https://downloads.claude.ai/model-catalog/v1/schema.json"` anchor at
  215173117 → brace-depth walk with string/escape tracking → full signed seed parsed
  (`model-catalog-seed.json`); the second registry at 199521935 → 21 models
  (`model-registry.json`); the aliases block (`best:"fable"`) at 199537503
  (`model-aliases.json`).
- Capability flags, pricing codes, `effort_cost_index`, `advisor_rank`, `min_claude_code_version`
  all quoted byte-exact from the registry literals; per-provider alias skew from the aliases
  block; staging URLs from `code-claude-docs.txt` (63 inventoried paths).
- Trial (2026-10-18): `extract_model_catalog.py` → exit 0 with the exact seed/registry
  anchors re-verified byte-exact on the live binary.

## 3. WHAT IT UNLOCKS

In plain terms: the binary's model catalog mixes public and internal-only families, and the
binary itself tells you which is which. Fable 5 and 5.1 are public models (launched June and
September 2026 — the catalog entries match Anthropic's public price list). Mythos 5/5.1 is
the genuinely internal one: every third-party provider ID is null, it has no public alias,
and public reporting says it only goes to vetted security partners. The real leak isn't a
secret flagship — it's the internal-only sibling's footprint: its capability flags, safety
mitigations bundle, and the version gates around it, sitting in a shipping binary. Tooling
can stop chasing aliases and pin models deliberately — including not pinning models that
this build is too old for.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Model pinning:** pin by full model ID (`claude-opus-5-5`, not `opus`) and check the
  `min_claude_code_version` gate first (opus-5-5 needs ≥2.1.280; fable-5-1 needs ≥2.1.251) —
  the picker drops older builds silently.
- **Cost awareness:** `effort_cost_index` gives real per-effort multipliers (e.g. sonnet-5
  max effort = 5.59x base); `maxEffortLevel` in settings clamps anything above a chosen
  ceiling on every provider. Pricing codes follow the `tier_X_Y[_cache_read_Z]` shape —
  use them for cost-tier bucketing, not dollar math (dollar mapping ungrounded).
- **Provider skew:** aliases resolve differently per provider (foundry "opus" = 4-6,
  gateway "opus" = 4-7) — if you need a specific model version on Bedrock/Vertex/Foundry,
  pin the full ID, not the alias.
- **Watch feed:** re-run `pocs/extract_model_catalog.py` against new builds and diff
  `version`, `issued_at`, model ids, and `disabled` flags — it is the earliest signal of a
  model launch, deprecation, or server-side kill-switch flip.
  ([pocs/outputs/model-table.md](sandbox://workspace/rea-claude/deep-dive/pocs/outputs/model-table.md))
- **Boundaries:** Mythos is internal-only (first_party ids only, no alias, not addressable);
  do not build tooling that assumes Mythos servability. `ccd`/`ccr` surfaces appear in the
  seed but their roles are ungrounded — treat as unknown.
