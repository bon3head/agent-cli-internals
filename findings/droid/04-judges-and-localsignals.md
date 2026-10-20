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

Expanded 2026-10-20 from web research. Every comparative claim below carries a
published source; where a practice could not be confirmed from a published source it
is marked UNCONFIRMED instead of asserted. No em dashes used anywhere in this file.

### (a) Per-vendor comparison: who watches what, and who holds the switch

| Tool | What user content leaves the machine | Any scoring/classification of the user | Who holds the switches | Source |
|---|---|---|---|---|
| Claude Code (Anthropic) | Prompts/outputs transit Anthropic infra by design; commercial products not used for training by default; API inputs/outputs auto-deleted within 30 days; consumer plans (Free/Pro/Max) since the Aug 2025 terms update can be used for training under an opt-out, retained up to 5 years; zero data retention available to enterprise orgs | None disclosed in product: no published per-user expertise scorer, no per-session user labels | The individual (training opt-out at claude.ai settings; /feedback is explicit); orgs via commercial terms and ZDR | Per third-party summaries of Anthropic's privacy center: https://www.claude3p.com/articles/trust-training-commitments ; https://terms.law/Privacy-Watchdog/ai-services/anthropic/ |
| Codex CLI (OpenAI) | Model traffic to OpenAI; anonymous usage/health metrics documented as containing no PII; OTel log/trace export is opt-in and prompt logging defaults off | None found: the Guardian judges planned actions, not the user; `codex_turn_event` carries fingerprints, not user scores | The individual: `[analytics] enabled = false` in config.toml, documented in the official docs; Business/Enterprise/API not trained by default | Official docs: https://learn.chatgpt.com/docs/config-file/config-advanced ; this repo's gated codex run (`findings/codex/15-gated-rerun.md`) |
| Cursor | Prompts/code/transcripts to Cursor backend and model providers; with Privacy Mode off, content may be used to improve/train; with Privacy Mode on, ZDR agreements with providers, nothing stored or trained on | None disclosed in product | The individual flips Privacy Mode; Business tier forces it ON org-wide (reduces collection, not adds) | Official: https://cursor.com/en-US/data-use |
| GitHub Copilot | Prompts, suggestions, engagement telemetry (accept/reject, cursor pos) retained up to 28 days; since Apr 24 2026, Free/Pro/Pro+ interaction data may train models unless opted out; Business/Enterprise never trained | None disclosed in product | Org (Business/Enterprise contractually exempt from training); individual opt-out at github.com/settings/copilot | https://deepwiki.com/github/site-policy/3.5-copilot-and-codespaces-privacy-statements ; https://completeaitraining.com/news/github-to-use-copilot-interaction-data-for-ai-model/ ; https://dev.to/max_quimby/github-copilot-is-now-training-on-your-code-heres-your-30-day-window-to-stop-it-4dmj |
| Cline (open source) | Model traffic via chosen provider/BYOK; built-in telemetry is anonymous PostHog events; never collects code, prompts, conversation content, file names, or credentials | None: telemetry is event counts only | The individual toggles telemetry; admins can force it OFF org-wide (the lock only restricts in one direction); always opt-in | Official: https://cline.bot/blog/introducing-anonymous-telemetry-in-cline ; https://docs.cline.bot/enterprise-solutions/monitoring/telemetry |
| Aider (open source) | Model traffic to chosen provider; analytics system redacts model names and paths, collects no code content, no chat messages, no API keys; anonymous UUID4 identity | None | The individual: `--analytics-disable` permanently disables, `--no-analytics` per session, `--analytics-log` for local-only | https://deepwiki.com/whisper0402/aider/9.1-analytics-and-reporting (citing aider/analytics.py); https://Aider.chat/docs/legal/privacy.html |
| Devin/Cognition (Windsurf's current owner) | Session content to Cognition infra; by default data may be used for model training; opt-out on paid plans; Enterprise never trained without written consent | None disclosed | Admins exercise the opt-out for Teams; individuals on other paid plans | https://windsurf.com/security (Cognition Devin docs, current publisher of Windsurf) |

Note on Windsurf: Windsurf's original privacy materials were superseded after its
acquisition; the live documentation is published by Cognition for Devin. Earlier
Windsurf-specific claims are therefore UNCONFIRMED from current published sources.

### (b) The workplace-monitoring angle

Droid is sold to organizations; the scored "user" is typically an employee of a
Factory customer, not the person who bought the software. Two facts make this angle
load-bearing:

1. **New York's electronic monitoring law (Civil Rights Law Section 52-c, in effect
since May 7, 2022).** Any private employer in New York that monitors or intercepts
an employee's "telephone conversations or transmissions, electronic mail or
transmissions, or internet access or usage" by any electronic device or system,
including a computer, must give prior written notice on hiring, acknowledged by the
employee, and must post the notice conspicuously. Enforcement sits with the state
attorney general; there is no private right of action. The required notice language
is a broad blanket: anything the employee does on any device "may be subject to
monitoring at any and all times and by any lawful means."
([text](https://newyork.public.law/laws/n.y._civil_rights_law_section_52-c*2),
[analysis](https://www.bpslaw.com/new-york-employee-monitoring-law-what-employers-need-to-know/)).
This is not legal advice. What it means as a category: a New York employer that
enables Droid's analytics controls becomes an employer running a tool that sends
employee work transcripts to a vendor for AI scoring, which is the kind of
monitoring the notice statute's categories describe. **The disclosure obligation
falls on the employer (Factory's customer), not on Factory or on the CLI.** A
blanket acceptable-use notice plausibly covers "internet usage"; what it does not
cover is per-employee expertise grades derived from verbatim conversations, because
no employer knows from the product that such grades exist. There is no client-side
surface where the employer learns the judge pipeline exists at all; the served
config it fetches is not a disclosure document.

2. **Factory's org-facing product sells the other end of this.** Factory's official
Analytics API is described as exposing "token consumption, tool use, user
activity, productivity signals, and per-user metrics"
([third-party write-up citing official docs](https://daisuke.masuda.tokyo/article-2026-08-11-1401)).
The recovered source confirms the org-facing half: the Agent Effectiveness report
command generates org-owner reports on agent usage and effectiveness, and the
persisted signals schemas are keyed to session identity. So the pipeline's output
is visible to the employer as per-user productivity metrics, while the employee
whose sessions generate those metrics has no product surface showing they were
graded. Among the vendors surveyed, no other coding tool documents per-user
productivity metrics derived from AI-scored transcripts; whether any does this
undisclosed is UNCONFIRMED.

### (c) The consent-structure comparison

Every surveyed vendor structures org-vs-individual control so the individual keeps
a veto over the sensitive direction: Codex defaults analytics off for the CLI and
gives the individual config.toml; Cursor lets the individual flip Privacy Mode and
lets Business only force it ON (toward less collection); Cline lets the individual
toggle telemetry and lets admins only force it OFF (toward less collection);
Copilot exempts Business/Enterprise from training contractually and gives
individuals an opt-out; Aider's analytics switches are all individual-level.

Droid inverts the pattern: the LocalSignals consent is an org managed-settings
field (`advancedAnalyticsEnabled`), enforced server-side, "intentionally excluded
from strict client writes." An org that enables it silently enrolls every member;
an org that disables it enrolls nobody. The individual developer has no setting,
no flag, no command, and no visibility. The consent subject is the organization;
the judged subject is the individual. Among surveyed tools, this is the only
consent structure where the party being scored has no control and no notice.

### (d) The third-party routing comparison

The judge's verbatim transcripts (up to 500k chars) route through Factory's LLM
proxy to a third-party model: `gpt-6-luna` (OpenAI family) by compiled-in default,
with `claude-haiku-5-5` (Anthropic) second on the preference list. The inference
happens at the provider, not at Factory. Compare: Cursor's Privacy Mode maintains
zero-data-retention agreements with its upstream providers; Copilot's data policy
states interaction data is not shared with third-party AI providers; Anthropic's
consumer data stays inside Anthropic. Droid's judge calls send verbatim user
transcripts to third-party inference as the pipeline's normal operation. What the
inference provider retains from these calls is not visible in client source and is
UNCONFIRMED; the routing itself is code-verified.

### (e) The research-vs-production contrast

Anthropic's paper "Agentic coding and persistent returns to expertise" (Hitzig,
Massenkoff, Lyubich, Heller, McCrory, published June 16, 2026) analyzed ~400,000
Claude Code sessions from ~235,000 users collected October 2025 to April 2026,
describing its method as privacy-preserving throughout
([Anthropic research page](https://www.anthropic.com/research/claude-code-expertise)).
Its published design: a Sonnet-based classifier graded sessions (including the same
novice-to-expert five-level shape), grades were cross-checked against telemetry
with >90% agreement, and results were published as aggregate findings, not as
per-user labels shipped to anyone
([independent walkthrough](https://dev.to/aidiveyt/anthropic-graded-400000-claude-code-sessions-managers-beat-the-engineers-j61)).
Droid ships the same analytical idea as a production pipeline: the same five-level
user-expertise scale, computed per session, persisted per session id, gated by org
consent the individual cannot see, and re-runnable by served config without a
release. The rubric source's provenance comment names this exact research and
notes its authors' own exclusions: occupation inference and dollar-value estimates
were "deliberately out of scope (privacy / calibration)." Factory's engineers kept
the per-session user scoring and shipped the parts their own comments flagged as
the privacy-sensitive ones.

### (f) Final verdict, facts assigned to tiers

**STANDARD (the industry baseline, confirmed across vendors).** Telemetry that
measures usage, errors, and adoption, with the individual holding a visible
switch: Codex's default-off analytics, Cursor's Privacy Mode, Cline's opt-in
anonymous events, Copilot's training opt-out and Business/Enterprise exemption,
Aider's CLI flags, Anthropic's training controls and 30-day API deletion. Droid's
own `telemetry.enabled: false` switch for its four Factory-bound legs belongs in
this tier. Nothing here is unusual.

**UNUSUAL (published products rarely do this, and none in the survey do it all).**
A per-session expertise label on the individual user, computed silently in
production, with no user-visible surface and no individual opt-out; up to 500k
chars of verbatim transcript routed through the vendor's gateway to a third-party
model specifically to grade the user; consent held entirely at the org level via a
server-managed field the individual cannot see or touch; the whole pipeline
steerable by served config, so what gets collected can change without a software
release; and a crash-reporting pipeline (Sentry) that ships with `sendDefaultPii:
true`, local-variables capture, and the user's full prompt in `process.argv` on
every event with no user off-switch in prod. Each of these is code-verified in
Droid and absent from the published product of every surveyed vendor.

**WITHOUT PUBLIC PRECEDENT among coding CLIs.** After searching published
documentation, policies, changelogs, and product surfaces across seven vendors: no
documented product maintains per-session novice-to-expert user scores keyed to
session identity, derived from verbatim user transcripts, routed through
third-party inference, persisted to the vendor, under org-gated consent invisible
to the individual, with no user-facing disclosure of the scoring. The closest
published system is Anthropic's own research classifier, which is exactly the
contrast: aggregated, privacy-preserving, one-off, published. Droid's is per-user,
persisted, production, and invisible.

**Earned caveats.** (1) The per-user expertise rollout is feature-flagged in
source and the flags default off; what we verify is the shipped mechanism, the
gating structure, and the served-config steerability, not how many orgs have it
enabled. (2) The "without precedent" claim is falsifiable: if a comparable public
product exists, the honest correction is that the claim is wrong, not that the
pipeline is standard. (3) Nothing in this section is legal advice; the NY statute
is described as a disclosure category, not as a conclusion about any party's
compliance.

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
