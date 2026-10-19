# 11 — Codenamed experiment gates + grounded feature families (C5)

> **Correction (2026-10-19, reinforcement):** the "128" figure is withdrawn as a count — no
> 128-list artifact exists and the number is filter-dependent/unreproducible. Independent
> re-enumeration finds **549 distinct gate names** (prior's 528 missed 21 real gates, incl.
> `tengu_kairos_cron`). The phenomenon (codenamed `tengu_*` experiment namespace) is VERIFIED;
> exact codenamed-form counts are not. Also: the experiment SDK is **GrowthBook**, not Statsig —
> every `tengu_*` gate is a GrowthBook evaluation (remoteEval against `https://api.anthropic.com/`
> with embedded SDK client key); see new doc `13-growthbook-experiment-sdk.md`.

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C5 (internal intel) · **Trial status:** no live PoC trial (gates were extracted
statically; no trial PoC covers them) — CONFIRMED at the byte level in REA.
**Confidence:** CONFIRMED (byte-level) for the gate inventory and grounded families. Feature-family
meanings beyond the grounded set (amber, cedar, juniper, slate, rotunda, basalt, async, atomic,
convolute) are ungrounded/unknown; `harbor_kite_cloud` needs an org UUID (env alone insufficient).

---

## 1. WHAT WAS FOUND

**549 distinct gate names** found on re-enumeration (prior said 528 — 21 real gates missed,
incl. `tengu_kairos_cron`); the codenamed `tengu_<adjective>_<noun>` form is the
staged-rollout/experiment namespace (full list in `gate-checks.txt`). Gates resolve server-side via an installed `featureGateLookup`
(`function $6o(e){eL().featureGateLookup=e}`; lookup returns `===!0` with the compiled local
default when unmapped); TTL form `iB(name, default, 300000)` (5-min cache).

Grounded samples (gate → what it gates, CONFIRMED context):

| gate | grounded to |
|---|---|
| `tengu_radiant_island` | effort-medium-nudge experiment for `claude-opus-5` (`from:["high"]`) |
| `tengu_steady_plum` | effort-medium-nudge for `claude-fable-5-1` (`from:["high","xhigh","max"]`; zod-validated served copy) |
| `tengu_pewter_owl_model` | remote model-routing override (`qd()?.pewter_owl_model` else gate value; env `CLAUDE_CODE_PEWTER_OWL`) |
| `tengu_curious_tower_stateless_models` | comma-separated allowlist of "stateless models" |
| `tengu_saffron_credits_only_tiers` | billing: `creditsOnlyTiers` allowlist (saffron = pricing/billing: `saffron_ladder`, `saffron_lattice`, `saffron_picker_dim`, `saffron_kite`, `saffron_wren`) |
| `tengu_smooth_harbor` | extra-usage billing (`cachedExtraUsageDisabledReason`) |
| `tengu_kairos_cron` / `tengu_kairos_cron_durable` | scheduled tasks — **killable via `CLAUDE_CODE_DISABLE_CRON`** |
| `tengu_harbor_kite_cloud` | cloud sessions (needs org UUID + `CLAUDE_CODE_HARBOR_KITE_CLOUD`) |
| `tengu_gleaming_fair` / `_reuse` | session-resume UI (`compact|continue|dismiss|never|cancelled`) |
| `tengu_wise_kite` | marketplace install policy (official-marketplace check) |
| `tengu_maple_sundial` | hidden slash-command enablement |
| `tengu_jade_compass` | compass-capability experiment |

Feature-area families (grounded): **`kairos`** = scheduling (cron, loops, push notifications,
briefs); **`harbor`** = cloud sessions + billing/limits (`harbor_kite`, `harbor_ledger`,
`harbor_permissions`); **`fleetview`** = background-agent roster; **`violin`** = cloud
remote-tools ("remote-tools gate (tengu_violin_wood)… absent outside cloud workers");
**`grove`** = policy/privacy UI; **`cobalt`** = artifacts (compliance-gated:
`deniedUnder:["hipaa","zdr"]`); **`lantern`** = session modes/wrap-up.

Version gates and rollout mechanics (CONFIRMED): per-model `min_claude_code_version`; release
channels `autoUpdatesChannel:()=>B(["latest","stable","rc"])` ("rc" rendered "slow"); user/org
`minimumVersion` anti-downgrade pin; org-policy minimum CLI floor; server-driven gates with
compiled local defaults; signed served catalog (`downloads.claude.ai/model-catalog/v1/catalog.json`
+ `.raw-sig.json`, SPKI-verified; compiled seed is the 7-day-expiry offline fallback);
per-model `disabled` kill-switch (currently `false` on the deprecated row).

**KILL:** "Experimental"/"Internal" as feature-maturity markers — they are just `/config` UI
tab labels (`var cn=["Appearance","Model & output",...,"Experimental","Internal"]`).

Also grounded in the same lane: embedded changelog is NOT in the binary — it is fetched at
runtime from `https://raw.githubusercontent.com/anthropics/claude-code/refs/heads/main/CHANGELOG.md`
(env override `CLAUDE_CODE_DEV_RAW_CHANGELOG_URL`) and cached per-user. INFERENCE: kairos
cron loops cost pressure is visible in the effort-nudge experiments (high→medium pushes) plus
`effort_cost_index` (sonnet-5 max = 5.59x).

## 2. HOW IT WAS FOUND

- Lane C5: string-table regex over the 343,861 unique strings → 2,735 `tengu_*` events
  (`tengu-events.txt`), 545 gate checks (`gate-checks.txt`); codename-form gates filtered
  from the set (count filter-dependent — see correction note); `featureGateLookup` install + check functions located by byte read.
- Grounding done gate-by-gate: each named gate above was traced to the function using it
  (e.g. `radiant_island` in the effort-nudge map `XO`, `wise_kite` in `c7()`), with the
  surrounding context quoted verbatim in `internal-intel.md`.
- Env-var overrides (`CLAUDE_CODE_PEWTER_OWL`, `CLAUDE_CODE_DISABLE_CRON`,
  `CLAUDE_CODE_HARBOR_KITE_CLOUD`, `VOICE_STREAM_BASE_URL`, `VERTEX_REGION_CLAUDE_*`) found
  adjacent to their gates.

## 3. WHAT IT UNLOCKS

In plain terms: the binary contains a live map of what Anthropic is A/B testing — effort
nudges, billing experiments, cron scheduling, cloud sessions, hidden slash commands. Several
of these have local environment-variable overrides, which means a developer can opt in (or
out) of experiments deliberately instead of being silently bucketed.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Local overrides (no server round-trip needed):** `CLAUDE_CODE_PEWTER_OWL=<model>` (remote
  model-routing override), `CLAUDE_CODE_DISABLE_CRON=1` (kills kairos scheduled tasks —
  useful in sandboxes/CI), `CLAUDE_CODE_HARBOR_KITE_CLOUD` (cloud-session gate, needs org
  UUID), `VOICE_STREAM_BASE_URL` (voice backend).
- **Experiment watchlist:** track `tengu-events.txt` / `gate-checks.txt` across builds —
  new codename gates are the earliest signal of an in-flight feature; gates that lose their
  checks between builds are shipped or killed.
  ([tengu-events.txt](sandbox://workspace/rea-claude/deep-dive/tengu-events.txt))
- **Billing forensics:** the `saffron_*` (pricing) and `harbor` (cloud/billing) families +
  `effort_cost_index` explain usage bills better than any public doc; pair with
  `modelPricing` in settings (org-contracted rates) for fleet cost control.
- **Rollout awareness:** the `disabled` kill-switch + served-catalog signature flow means
  models and features can appear/disappear without a client release — build health checks
  that read the *served* catalog (`catalog.json`), not the compiled seed (expired 2026-10-08).
- **Don't chase:** `amber`, `cedar`, `juniper`, `slate`, `rotunda`, `basalt`, `async`,
  `atomic`, `convolute` namespaces are ungrounded — treat any claim about them as unverified.
