# 10. Safety machinery: Droid Shield's three layers and the shadow risk classifier

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source. Full texts: [prompts/droid.md §3.1–3.3, §3.8](../../prompts/droid.md#3-safety--security).

> **Correction (2026-10-20, source-gated):** the lane docs said "Shield = deterministic +
> fallback secret-risk model". Source says **three layers**: deterministic regex scanner +
> `[Risk]` fallback secret-risk finetune + `[Downgrade]` false-positive triage finetune
> (`packages/common/src/api/droid-shield/constants.ts:48-82`). Verdicts come from token-logprob
> softmax (thresholds 0.95/0.3775, `src/api/droidShield.ts:79-98`); the pipeline is fail-closed.

## WHAT WAS FOUND

**The op-risk classifier is shadow-only.** The independent operation-risk classifier
(5,858 chars source; [full text](../../prompts/droid.md#38-operation-risk-classifier-full--bundle-only-no-string-table-twin))
runs fire-and-forget at a single call site (`src/agent/tools.ts:1637`), gated by a Statsig
flag defaulting **off**, with the written contract "must not use the independent result for
enforcement" (`RiskClassificationService.ts:114-119`). The live approval path uses the
model-authored `riskLevel`. Earlier docs called it a "pre-execution risk gate" - corrected.

**The catastrophic tables are exact and hardcoded**: `DEFAULT_RM_DENYLIST` (10 entries),
`DEFAULT_COMMAND_DENYLIST` (U + 22, incl. mkfs/dd/fork-bombs/PowerShell destructive set),
`RUNTIME_SAFEGUARD_DENYLIST_DEFAULTS` (named groups) - `packages/common/src/policy/constants.ts`.
`RiskAssessmentJudge` is NOT the op-risk wiring: it's the **PR-risk judge** experiment
(keyed on `pullRequestID`; backend-side `GET /api/internal/pr-risk/judge`) - corrected.

Kill-guard wrapper: embedded shell tooling (@94939076, noted not quoted in full). Airgap
mode's runtime-context block doubles as the airgap signal: it also stops Sentry init and
cloud sync.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

Shield was found in the prompt lane; BRUTE-MAX and the gate rebuilt the layering from
source. The design choice is the story: Factory ships a three-layer learned scanner that
runs for real, next to a second classifier it deliberately keeps in shadow mode. If you
wrap droid in your own approval pipeline, the only enforcement-adjacent model signal is
the model-authored one - the independent check never blocks.
