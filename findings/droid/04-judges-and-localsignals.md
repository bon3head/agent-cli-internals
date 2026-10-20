# 04. Factory-Judge: one persona, three rubrics - including a judge that scores the user

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered original source. Full prompt texts:
[prompts/droid.md §3.5](../../prompts/droid.md#35-analytics-judges--session-scoring-prompts-run-over-transcripts).
Source paths below are in the recovered tree (`runs/droid/source/`).

> **Correction (2026-10-20, source-gated):** the lane docs said "three hidden judges". Source
> says one persona, three rubrics: `packages/utils/src/signals/rubrics.ts` defines
> `intent_completeness` (:51), `friction` (:201), and `expertise` (:287), all opening
> "You are Factory-Judge, an analytics system that …". The dual pairing is a runtime cache
> optimization (`PAIRED_COMPACTION_VARIANT`, `src/services/local-signals/constants.ts:20`).

## THE WATCHING: what triggers an evaluation

Exactly three triggers exist, exhaustive by schema
(`LocalSignalsTriggerReasonSchema`, `packages/common/src/api/v0/local-signals/schemas.ts:36-41`):

- `compaction` - fires when the session context compacts
  (`src/hooks/compaction/flows.ts:66`). Window type SNAPSHOT (the pre-compaction transcript).
- `todo_completion` - fires when a todo batch completes
  (`src/services/local-signals/todoCompletionSignal.ts:56`). Window type TAIL (only the new tail).
- `session_end` - fires once as the session closes (exit, clear, logout, daemon close).
  Window type SNAPSHOT. No compiled-in rubric lists it; orgs opt rubrics in through the
  served Local Signals config's `triggers` map
  (`src/services/local-signals/constants.ts:24-48`).

**Watermarking (non-overlapping slices).** Dedup is keyed per (session, rubric)
(`LocalSignalsService.ts:601-694`): incremental rubrics on a tail trigger classify only the
tail added since their last classified message; whole-window rubrics skip when the end
message id matches the last classified one. Watermarks live in memory, a local sidecar
file, and the server's coverage record (`GET /api/v0/sessions/[sessionId]/local-signals`
returns per-rubric covered end message ids), so re-classifying an already-judged slice
never happens even across machines. A pass scores a fresh, non-overlapping window rather
than re-judging the whole conversation every trigger.

**The 500k-char verbatim budget.** The serialized transcript is clamped at
`LOCAL_SIGNALS_MESSAGE_MAX_CHARS = 500_000`
(`packages/common/src/api/v0/local-signals/constants.ts:112`). Conversational **text
blocks pass through verbatim, never redacted** (`serializeForClassifier.ts:256`).
Tool payloads are shown only when a rubric opts in: `toolPayloads: true` for
`intent_completeness`, `false` for friction and expertise
(`packages/utils/src/signals/constants.ts:20-38`), and shown payloads get
`scrubSecrets`. Excluded from prompt counts and from judgment context: injected user-role
messages (`llm_only`), hook batches, `user_only` notices, tool_result-only messages
(`packages/utils/src/messages/windowMetrics.ts` - the "is this a human prompt" filter).

## THE GRADING: the complete grading vocabulary

### Rubric 1: intent_completeness (did the assistant achieve the user's intent)

Intent taxonomy (13 primaries, sub-intents on 5): `code_generation`, `debugging`,
`code_review`, `knowledge_qa`, `devops`, `data`, `documentation`, `research`, `planning`,
`automation`, `agent_config`, `noise`, `other`. This rubric is also Factory's artifact
miner: it extracts PR URLs, Linear/Jira ticket ids and URLs, GitHub/GitLab issue URLs,
document kinds/URLs/titles, and Notion page URLs - all identifiers returned verbatim from
the transcript. Labels: `intentSuccess`/`requestFulfillment` in {Complete, Partial,
Failed}; `processCompliance` in {OK, MinorIssues, MaterialViolation};
`evidenceConfidence` in {High, Medium, Low}.

### Rubric 2: friction (what actually harmed the user's experience)

Severity scale: **High** (task blocked, abandoned, substantial rework, clear frustration),
**Medium** (noticeably slowed, real workaround, overcome at meaningful cost), **Low**
(minor hiccup, small real delay). When in doubt, the lower level.
Primary-cause categories: `usage_limit_billing`, `provider_error`, `platform_gate`,
`tool_defect`, `environment`, `agent_behavior`, `interruption`, `orchestration`,
`external_service`, `other`. Each friction moment must cite at least one per-message id
(`relatedEventIds`); no citation, no report.

### Rubric 3: expertise (THE USER IS GRADED)

The prompt's own instruction: "Judge the user, not the assistant." Full scale verbatim:

- `novice`: vague goal statements; cannot evaluate the assistant's output; accepts whatever
  is produced; asks the assistant to explain basics.
- `advanced_beginner`: knows what they want but not how; framing uses product-level
  language; corrections are outcome-based ("it doesn't work"), not technical.
- `intermediate`: frames tasks with some correct technical vocabulary; spot-checks output;
  catches obvious problems; sometimes redirected by the assistant.
- `advanced`: precise technical framing (names files, APIs, constraints); verifies output
  against their own mental model; corrects the assistant with specific technical reasons.
- `expert`: anticipates pitfalls before they occur; states constraints and edge cases up
  front; corrections are surgical and usually right; delegates deliberately while retaining
  design authority.

Also scored per window: `planningShareUser` and `executionShareUser` (integer 0-100, the
user's share of planning vs execution decisions), `successSignalStrength` and
`failureSignalStrength` (each 0-5), `evidenceConfidence` (High/Medium/Low), and a
`rationale` in the judge's own words.

This rubric adapts Anthropic's published "Agentic coding and persistent returns to
expertise" research (the source comments name it, with occupation inference and
dollar-value estimates "deliberately out of scope (privacy / calibration)"). Factory kept
the per-session user scoring and dropped the parts its own engineers flagged as private.

## THE SENDING: the two-step exfiltration

**Step one: the verbatim transcript goes to a judge model.** The client builds the rubric
prompt plus the serialized window (up to 500k chars, text verbatim) and sends it through
Factory's LLM proxy. The model is chosen from a preference list, org-configurable first:
`gpt-6-luna` (High effort) is the compiled-in default, then `claude-haiku-5-5`,
`glm-5-3-flash`, `deepseek-v4-1-flash`, `gpt-5-6-luna`, `claude-sonnet-5-5`
(`packages/utils/src/llm/constants.ts:286-303`). These are third-party models: the
request routes through Factory's gateway but the inference happens at the provider.
The source pins friction/expertise rollout behind feature flags that default off
(`isLocalSignalsRubricEnabled`, `src/services/local-signals/model.ts:70-81`); the
intent rubric is enabled for any org whose served config turns the pipeline on.

**Step two: paraphrased classifications are POSTed to Factory.** The client stamps the
judge's JSON (provenance: rubricId, rubricVersion, model, variant) and POSTs to
`/api/v0/sessions/[sessionId]/local-signals` with: `triggerReason`,
`messageRange` (start/end message ids, message count, truncated flag),
`classifiedAt`, the classification (paraphrased, "never quote" enforced on the output
side; the only verbatim content allowed back is URLs, ticket ids, document titles),
`windowMetrics` (content-free counts: userPromptCount, assistantActionCount,
assistantOutputChars), and `droidVersion`
(`PersistLocalSignalsRequestSchema`, `schemas.ts:440-453`).

The friction/expertise pair is billed once on the compaction path via prompt-caching
(`paired_compaction_v1`), so your transcript is read once and scored twice.

## THE SWITCHES: who controls this, and can you stop it

The client-side gate is a **server-served dynamic config**:
`isLocalSignalsClassificationEnabled()` reads the org's `local_signals_config_v0`
(`src/services/local-signals/model.ts:49-52`). The comment says it plainly: enabled is
"computed server-side as the Statsig rollout gate AND the org opt-in." The org's config
also controls, per rubric, which triggers fire, whether tool payloads are shown, and
whether multi-artifact arrays are collected, all without a CLI release. No
`telemetry.enabled` check appears anywhere in this client path; the served config is the
only client-side gate, and the server enforces the org opt-in.

**Can an individual user stop it?** From the source: no. There is no user-facing switch,
no settings key, no command, and no UI surface that shows a user they were judged.
The "consent" is the org's managed-settings field
(`advancedAnalyticsEnabled === true && (consentVersion === 1 || localSignalsOptIn === true)`,
`packages/common/src/settings/schema.ts:1259-1267`), written by the backend when an org
owner enables the unified control, "intentionally excluded from strict client writes."
An org that turns it off kills the pipeline for its whole team; an org that leaves it on
means every member's sessions are scored, silently.

## THE OTHER GRADERS: do not confuse these with the user judge

- **Agent Readiness auditor** (`packages/common/src/agentReadiness/schemas.ts`): scores
  the AGENT, not the user. An auditor agent evaluates readiness signals as
  numerator/denominator pairs with rationales and uploads them to
  `POST /api/organization/agent-readiness-reports` (repoUrl, sessionId, commitHash
  included). A QA harness for the product.
- **Agent Effectiveness report** (`src/commands/agent-effectiveness-report.ts`): an org
  owner/manager slash command that generates a report on agent usage and effectiveness
  for the organization, entitlement-gated. Org-facing analytics about the agent.

Both are visible, opt-in surfaces about the agent. Factory-Judge is an invisible,
org-gated pipeline about the user. Different subjects, different visibility.

## HOW FACTORY GRADES ITS USERS

This section is written for a non-expert. Every claim above is sourced in the sections
before it.

When you use Factory Droid, and your organization has switched on its analytics
controls, the program quietly sends your conversation to a second AI and asks it to
grade you. The grade has five levels. At the bottom, you are a "novice": vague goals,
you accept whatever the program produces, you ask it to explain basics. At the top,
you are an "expert": you anticipate problems, you state constraints up front, your
corrections are surgical and usually right.

It also records how much of the planning you did versus the assistant (0 to 100), how
much of the execution you did, and how strong the evidence of success or failure is
(0 to 5). It logs your moments of friction: errors, going in circles, frustration, each
tagged with a cause like billing limits, platform restrictions, or your own mistakes.

Your words travel to the grader verbatim, up to half a million characters per pass, and
the grader may be a model run by a third party, not by Factory itself. What comes back
and gets stored is a paraphrased scorecard, attached to your session id. Nobody tells
you this happened. There is no screen, no setting, no command that shows you your
grade or lets you opt out. Your employer controls the switch. If they leave it on, you
are scored. If they turn it off, you are not.

## DUBIOUSNESS VERDICT (judgment, grounded in published practice)

**STANDARD (the industry baseline):** telemetry with switches. OpenAI's Codex CLI ships
analytics default-off for the CLI with an explicit `analytics.enabled = false` opt-out,
and its OTLP export is opt-in with prompt logging defaulting off
(`log_user_prompt = false`). Anthropic publishes retention and training controls for
Claude Code (consumer opt-out of training, 30-day back-end deletion, ZDR for
enterprise). Cursor has a user-facing Privacy Mode toggle (forced on for Business).
Every one of these is a control the individual can see and flip.

**UNUSUAL:** a per-session expertise label on the individual user, computed silently in
production, with no user-visible surface and no individual opt-out; up to 500k chars of
verbatim transcript routed through the vendor's gateway to a third-party model
specifically to grade the user; consent held entirely at the org level via a
server-managed field the individual cannot touch; and the whole pipeline steerable by
served config, meaning what gets collected can change without a software release.

**WITHOUT PUBLIC PRECEDENT among coding CLIs:** I searched for comparable tooling and
found none published: no documented product that maintains per-session
novice-to-expert user scores keyed to session identity, derived from verbatim user
transcripts, inside a shipped CLI, under org-gated consent invisible to the individual.
Anthropic's own research on this exact question ("Agentic coding and persistent returns
to expertise," ~400,000 sessions from ~235,000 users, June 2026) was published as
aggregated, privacy-preserving research, not as a per-user production scoring pipeline.
Factory's engineers even noted in their own comments that the paper's occupation
inference and dollar-value estimates were "deliberately out of scope (privacy /
calibration)" - and then shipped the per-user scoring anyway.

This verdict is my judgment laid over the code facts. The code facts are the sections
above. If a comparable public product exists and I missed it, the honest correction is
that the "without precedent" claim is wrong, not that the pipeline is standard.

## Open questions

- What the server-side signals-async engine feeds its model when it re-runs the same
  rubric bodies (the bodies are shared with the CLI; the server's window contents are
  not verifiable from the client source).
- Retention and access policy for stored classifications on Factory's side (server code
  is not in the binary).
- Whether org dashboards surface per-user expertise labels or only aggregates.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

Prompt lane (judge text @94987054), brute-force waves (LocalSignals consent transform),
gate re-derivation from `rubrics.ts` + `LocalSignalsService.ts`, and the October 2026
deep-dive that executed the pipeline's serialization code in bun and walked the full
wire path. Anyone scored by this pipeline - every user whose org enables it - is being
graded by a judge they were never told about, on a rubric that explicitly scores *them*.
