# 04. Factory-Judge: one persona, three rubrics - including a judge that scores the user

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source. Full prompt texts: [prompts/droid.md §3.5](../../prompts/droid.md#35-analytics-judges--session-scoring-prompts-run-over-transcripts).

> **Correction (2026-10-20, source-gated):** the lane docs said "three hidden judges". Source
> says one persona, three rubrics: `packages/utils/src/signals/rubrics.ts` defines
> `intent_completeness` (:51), `friction` (:201), and `expertise` (:287), all opening
> "You are Factory-Judge, an analytics system that …". The dual pairing is a runtime cache
> optimization (`PAIRED_COMPACTION_VARIANT`, `src/services/local-signals/constants.ts:20`).

## WHAT WAS FOUND

**The `expertise` rubric judges the USER, not the assistant** - its prompt says so verbatim
("Judge the user, not the assistant"). It scores user expertise/friction from session
transcripts. Triggers: `session_end`, `compaction`, `todo_completion`
(`LocalSignalsTriggerReasonSchema`, `packages/common/src/api/v0/local-signals/schemas.ts:36-41`;
call sites in `flows.ts:63`, `todoCompletionSignal.ts:61`, `LocalSignalsService.ts:1476`).

**No redaction on conversational text.** Conversational text passes to the judge verbatim -
never redacted (gate-refined: tool payloads get `scrubSecrets` only when a rubric opts in -
`toolPayloads: true` for `intent_completeness`, false for friction/expertise). Output-side:
rubrics require "Paraphrase, never quote"; persisted JSON carries no raw transcript.
Classifications are POSTed to Factory's backend. The pipeline is server-steerable per org
without a release.

**Consent gate is an org-settings field:** `advancedAnalyticsEnabled === true &&
(advancedAnalyticsConsentVersion === current || localSignalsOptIn === true)`
(verbatim, `packages/common/src/settings/schema.ts:1259-1267`), and it lives in
`ManagedSettingsSchema` - **the org controls it**. `ADVANCED_ANALYTICS_CONSENT_VERSION = 1`.

## INTERNAL VIEW: a worked session example

What Factory's internal side sees when the pipeline fires (reconstructed from the source,
not observed traffic - the gate did not run a live judge):

1. Session ends (or compacts, or a todo batch completes). `LocalSignalsService` builds the
   trigger envelope: trajectory blocks (conversational text verbatim; tool payloads scrubbed
   only for `intent_completeness`), session metadata, `sessionId`.
2. One persona is invoked with three rubric variants. The `expertise` call returns a score
   of *your* competence; `friction` returns moments the agent struggled.
3. Results are persisted as paraphrased JSON (no raw transcript) and POSTed to Factory's
   analytics backend; orgs can receive per-session quality/telemetries without a release.
4. The consent gate consults the **org's managed settings** first: an org that turns off
   `advancedAnalyticsEnabled` kills the pipeline for its whole team; an org that leaves it
   on means every member's sessions are scored.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

Prompt lane (judge text @94987054), brute-force waves (LocalSignals consent transform),
gate re-derivation from `rubrics.ts` + `LocalSignalsService.ts`. Anyone scored by this
pipeline - every user whose org enables it - is being graded by a judge they were never told
about, on a rubric that explicitly scores *them*. The one-line fix for operators: read
`schema.ts:1259-1267` and decide who controls `advancedAnalyticsEnabled`.
