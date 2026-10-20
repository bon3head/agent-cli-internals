# Droid crosswalk: surface ↔ internals

Target: Droid v0.245.0, sha256 `61ad343a…fa18177cd`. Read the agent's mind at any
moment: left column is what you see, the next two columns are the exact prompt and the
exact mechanism, right column is what actually happens. Source paths are the recovered
original source (`runs/droid/source/`), all verified present.

## 1. Modes

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| M1 | Interactive TUI | the terminal app | [§1.6 Harness](../../prompts/droid.md#16-main-prompt-section-harness-fragment) | `src/` TUI; `src/keyboard/` vim reducer | keystroke reducer + pane preemption; locale one-liners drive the autonomy picker |
| M2 | `droid exec` | one-shot non-interactive run | [§2.2 tier semantics](../../prompts/droid.md#22-per-tier-semantics-from-droid-exec-help-examples) | `src/entrypoints/exec/command.ts` | full help text verbatim @99916500; 31 options |
| M3 | Mission mode (`--mission`, `/missions`) | workstream swarm | [§1.2 mission orchestrator](../../prompts/droid.md#12-non-interactive-mission-orchestrator) | `src/services/droids/BuiltInDroidConfigs.ts` | orchestrator spawns listener + item-handler agents per workstream |
| M4 | `droid daemon` | background agent host | — | [CONFIG §6](./01-config-and-permissions.md#6-daemon-internals-and-e2e-hooks-wave-3); `src/entrypoints/daemon/handler.ts` | 167 `daemon.*` RPC methods; IPC or `--remote-control` via relay |
| M5 | ACP mode (`--output-format acp`) | editor agent protocol (Zed) | — | `src/acp/AcpAgent.ts` | org policy caps enforced here; formats `zed://` resource links |

## 2. Autonomy

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| A1 | Tiers off/low/medium/high | autonomy picker | [§2](../../prompts/droid.md#2-autonomy-tiers-priority-section), [§2.1 picker](../../prompts/droid.md#21-level-picker-descriptions) | `src/agent/autonomy.ts` (`getRequiredAutonomyLevel`); `packages/droid-sdk-core/src/protocol/shared/enums.ts:20-30` | off=you control all actions, low=edits+read-only, medium=reversible commands, high=all commands |
| A2 | `--auto` | raises auto-approval level | [§2.2](../../prompts/droid.md#22-per-tier-semantics-from-droid-exec-help-examples) | `src/entrypoints/exec/assertValidOptions.ts` (mutually exclusive with `--skip-permissions-unsafe`) | sets the Execute tool's command-risk auto-approval level, NOT which tools are available |
| A3 | `--skip-permissions-unsafe` | "dangerous commands, isolated envs only" | [§2.4](../../prompts/droid.md#24---skip-permissions-unsafe-semantics); [CONFIG §3](./01-config-and-permissions.md#--skip-permissions-unsafe-recovered-semantics-yes) | `ExecRuntimeConfigService.ts:61-66` → `shouldConfirmExecution.ts:619-622` | disables only the **confirmation** layer; blocklists, policy preflight, hooks still fire |
| A4 | Reserved destructive class | "Re-run with --auto high… or --skip-permissions-unsafe" ladder | [§2.4](../../prompts/droid.md#24---skip-permissions-unsafe-semantics) | `shouldConfirmExecution.ts:761`; `packages/utils/src/rules/runtimeSafeguards.ts` | hard `block` can never run and never be approved, even under A3 |
| A5 | Spec mode (`--mode spec`) | research before implementing | [§2.6](../../prompts/droid.md#26-spec-mode-prompt-text) | `modeDescriptions` locale object | auto / spec / mission one-liner presets |

## 3. Agents & workstreams

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| W1 | Workstream listener | mission coordination agent | [§1.12](../../prompts/droid.md#112-mission-workstream-listener-opening-prompt--bundled-skill) | workstream-listener skill asset @267742278 | opening prompt + bundled skill, per-workstream |
| W2 | Item handler | per-item worker | [§1.13](../../prompts/droid.md#113-mission-workstream-item-handler-per-item-agent-prompt) | item-handler skill asset @267753069 | dispatched per workstream item |
| W3 | Recurring-loop persona | idle recurring agent | [§4.11](../../prompts/droid.md#411-recurring-loop-idle-persona-full) | `loop` i18n namespace | "running on a recurring loop with no specific task assigned" |
| W4 | `/security-review` | thorough-tier auditor | [§B.1](../../prompts/droid.md#b1-security-review-thorough-tier--the-security-review-document-head-265837870) | UTF-16LE skill asset @265837870 | UTF-16LE-only skill-asset cluster, 265.5–267.8M |
| W5 | Slack triage agent | triage automation | [§B.2](../../prompts/droid.md#b2-slack-triage-agent-full-document-head-266799878-16122-chars) | UTF-16LE skill asset @266799878 (16,122 chars) | full triage playbook |
| W6 | Severity rater | scores finding severity | [§B.3](../../prompts/droid.md#b3-independent-security-severity-rater-full-section-of-the-b1-document-head-266121306) | UTF-16LE skill asset @266121306 | embedded section of the §B.1 document |
| W7 | Novelty reducer | dedupes findings | [§B.0 census](../../prompts/droid.md#b0-census-of-heads) | UTF-16LE cluster (`extracts/utf16-*.md`) | head verified, full text in extracts |
| W8 | PR-risk scorer | scores PR risk | [§B.0 census](../../prompts/droid.md#b0-census-of-heads) | `builtin-skills/pr-risk-assessment/SKILL.md` — **NOT recovered** (H3 in gate ledger) | only kill-switch + experiment wiring known |
| W9 | `dogfood` skill | "systematically explore a web app" | [CONFIG §5](./01-config-and-permissions.md#5-internal-notes-and-hidden-flags) | skill asset @282223838; Rust `agent-browser` binary | internal QA workflow, shipped to every user |
| W10 | refactoring-playbook | mission skill | [wave-3 annex](../../prompts/droid.md#annex-wave-3-audit-2026-10-20-two-undocumented-builtin-mission-skills--internal-qa-prompts) | `src/skills/builtin/constants.ts:2516` | characterization testing, strangler fig, incremental migration |
| W11 | tui-application-playbook | TUI missions | [wave-3 annex](../../prompts/droid.md#annex-wave-3-audit-2026-10-20-two-undocumented-builtin-mission-skills--internal-qa-prompts) | `src/skills/builtin/constants.ts:2721` | vertical slices, walking skeleton, tuistory verification |
| W12 | Mission validator family | validates mission specs | [§A.3](../../prompts/droid.md#a3-mission-validator-family-utf-16-fragments-string-table-957961m) | UTF-16 fragments 95.7–96.1M | bundled validator rubrics |
| W13 | Agent Effectiveness | org usage report (org owners) | [§4.7](../../prompts/droid.md#47-agent-effectiveness-report-skill-org-owner-feature-condensed) | `get_agent_effectiveness_usage` tool | report rendered locally; "do not upload" vendor metadata to Factory |

## 4. Safety machinery

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| S1 | Droid Shield | secret scan on staged commits | [§3.1](../../prompts/droid.md#31-droid-shield--secret-detection-triage-model-full), [§3.2](../../prompts/droid.md#32-droid-shield--fallback-secret-risk-model-full) | `packages/common/src/api/droid-shield/constants.ts:48-82`; `src/api/droidShield.ts` | THREE layers: deterministic regex + `[Risk]` fallback + `[Downgrade]` triage; logprob verdicts |
| S2 | Op-risk classifier | silent risk scoring | [§3.8](../../prompts/droid.md#38-operation-risk-classifier-full--bundle-only-no-string-table-twin) | `src/services/RiskClassificationService.ts`; `packages/common/src/policy/constants.ts:24` | **shadow only**, default off; "must not use the independent result for enforcement" |
| S3 | Catastrophic tables | blocked destructive commands | [§3.8](../../prompts/droid.md#38-operation-risk-classifier-full--bundle-only-no-string-table-twin) | `DEFAULT_RM_DENYLIST` (10), `DEFAULT_COMMAND_DENYLIST` (U+22), `RUNTIME_SAFEGUARD_DENYLIST_DEFAULTS` | exact deny tables |
| S4 | Factory-Judge | scores sessions/user on triggers | [§3.5](../../prompts/droid.md#35-analytics-judges--session-scoring-prompts-run-over-transcripts) | `packages/utils/src/signals/rubrics.ts`; `src/services/LocalSignalsService.ts` | ONE persona, three rubrics: intent_completeness, friction, expertise ("Judge the user, not the assistant") |
| S5 | LocalSignals consent | org analytics gate | [§3.5](../../prompts/droid.md#35-analytics-judges--session-scoring-prompts-run-over-transcripts); [TELEMETRY annex](./02-telemetry.md#gate-errata--annex-source-recovery-2026-10-20) | `packages/common/src/settings/schema.ts:1255-1269` (`ADVANCED_ANALYTICS_CONSENT_VERSION=1`) | org-settings field: `enabled===true && (version===1 || localSignalsOptIn===true)` |
| S6 | permissionRules | declarative allow/ask/block | — | [CONFIG §3](./01-config-and-permissions.md#permissionrules-declarative-rule-layer-settings); `PERMISSION_RULES_CONFIG_VERSION=1` | `{version, rules}` container |
| S7 | PreToolUse hooks | allow/deny/ask interception | — | [CONFIG §3](./01-config-and-permissions.md#3-permission-model); `src/agent/tools.ts:1501-1540` | precedence block > ask > allow > no-match |
| S8 | Whole-process sandbox | isolated execution | [§3.7](../../prompts/droid.md#37-airgap-runtime-context-block-fragment) | [CONFIG §3](./01-config-and-permissions.md#whole-process-sandbox); `src/sandbox/constants.ts` | possession of the guard FD is the capability; env scrubbed |
| S9 | Kill-guard wrapper | shell tooling | [§3.6](../../prompts/droid.md#36-kill-guard-wrapper-embedded-shell-tooling-noted-not-quoted-in-full) | bundle shell tooling @94939076 | embedded tool wrapper, not quoted in full |
| S10 | Airgap mode | airgap runtime context | [§3.7](../../prompts/droid.md#37-airgap-runtime-context-block-fragment) | runtime-context block in prompt | airgap also stops Sentry init and cloud sync |

## 5. Data & billing

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| D1 | Alloy router | model choice per turn | [§A.1](../../prompts/droid.md#a1-the-model-router-classifier-prompt-new--utf-16-only-absent-from-earlier-sections) | `packages/droid-core/src/model-router/classifiers/prompt.ts`; `selector.ts` | per-turn LLM classifier, default gpt-5.4-mini, cheapest scoring ≥0.7 |
| D2 | Cost registry | billing multipliers | — | `packages/utils/src/llm/model-registry.ts` (109 blocks: 107 models + 2 shield) | multipliers only; margin not computable (no base rates) |
| D3 | `droid stats` badges | gamified usage stats | — | [CONFIG §5](./01-config-and-permissions.md#user-stats-badges-and-the-hidden-dataset-plus-experiments-entrypoints-closure-wave-2026-10-20); `packages/runtime/user-stats/src/parser.ts` | computed **locally only**; zero network |
| D4 | ExitCourier | invisible exit delivery | — | [TELEMETRY §ExitCourier](./02-telemetry.md#exitcourier-the-exit-time-delivery-channel-closure-wave-2026-10-20); `src/services/exitCourier/schemas.ts` | plaintext NDJSON spool `~/.factory/exit-spool/`; http/cloud-sync(incl. full message bodies)/reap |
| D5 | Sentry crash reports | invisible | — | [TELEMETRY annex](./02-telemetry.md#gate-errata--annex-source-recovery-2026-10-20); `src/sentry.config.ts:85-121` | `sendDefaultPii:true`, argv (incl. exec prompt), local vars; no user off-switch |
| D6 | Telemetry consent | `telemetry.enabled` | — | [TELEMETRY kill switches](./02-telemetry.md#kill-switches); `src/telemetry/consent.ts` | user `false` → Denied on 4 legs; org `true` overrides the denial |
| D7 | machineId | identity | [TELEMETRY identity fields](./02-telemetry.md#identity-fields) | `src/utils/cliTelemetryClient.ts`; `src/entrypoints/daemon/handler.ts:444-449` | daemon-protocol identity, **unhashed**; install id is a randomUUID |

## 6. Hidden internal tooling

| # | Surface item | What the user sees | Prompt section | Internal mechanism | Under the hood (one line) |
|---|---|---|---|---|---|
| H1 | `droid dataset` | (hidden) | — | [CONFIG §5](./01-config-and-permissions.md#user-stats-badges-and-the-hidden-dataset-plus-experiments-entrypoints-closure-wave-2026-10-20); `src/entrypoints/dataset/command.ts` | Factory-internal eval-dataset authoring, `AutoEvalPipeline` flag |
| H2 | `droid experiments` | (hidden) | — | same; `src/entrypoints/experiments/command.ts`; `/api/v0/experiments` | experiment ledger, `ExperimentLedger` flag |
| H3 | `exit-courier` | (hidden entrypoint) | — | [TELEMETRY §ExitCourier](./02-telemetry.md#exitcourier-the-exit-time-delivery-channel-closure-wave-2026-10-20); `src/entrypoints/exit-courier/command.ts` | registered hidden in `src/cli.ts:125` |
| H4 | FACTORY_E2E_* hooks | (hidden) | — | [CONFIG §1](./01-config-and-permissions.md#5-internal-notes-and-hidden-flags) | fault injection: crash-on-prompt, disk faults, slow paths, clock |
| H5 | Mission handoff record | handoff files | [§4.6](../../prompts/droid.md#46-mission-handoff-record-schema-fragment) | session dirs (`progress_log.jsonl`, `handoffs.jsonl`) | mission state persistence |

## Reverse index: internal code → what it's for

| Module | Surface items |
|---|---|
| `src/agent/autonomy.ts` | A1 tiers, A2 `--auto` |
| `src/agent/tools.ts` | S7 hooks, S2 classifier call site, A3 policy preflight |
| `src/telemetry/consent.ts` | D6 telemetry consent |
| `packages/utils/src/signals/rubrics.ts` | S4 Factory-Judge prompts |
| `src/services/LocalSignalsService.ts` | S4 judge pipeline, S5 consent gate |
| `src/sentry.config.ts` | D5 Sentry |
| `src/services/exitCourier/` | D4 ExitCourier (rows S4-S5 pipeline also lands here via spool) |
| `packages/droid-core/src/model-router/` | D1 Alloy router |
| `packages/utils/src/llm/model-registry.ts` | D2 cost registry |
| `src/services/RiskClassificationService.ts` | S2 op-risk shadow |
| `packages/common/src/api/droid-shield/constants.ts` + `src/api/droidShield.ts` | S1 Droid Shield |
| `src/entrypoints/daemon/handler.ts` | M4 daemon, D7 machineId |
| `src/acp/AcpAgent.ts` | M5 ACP mode |
| `src/entrypoints/exec/command.ts` + `assertValidOptions.ts` | M2 exec, A2/A3 flag validation |
| `src/services/droids/BuiltInDroidConfigs.ts` | M3 mission mode, W1/W2 workstreams |
| `src/entrypoints/dataset/command.ts`, `src/entrypoints/experiments/command.ts` | H1, H2 |
| `packages/runtime/user-stats/` | D3 stats/badges |
| `packages/common/src/feature-flags/constants.ts` | 317 flags (D2 adjacent), W8 kill-switch |
| `src/sandbox/constants.ts` | S8 sandbox |
| `src/skills/builtin/constants.ts` | W10, W11 playbooks |
| `packages/updater/src/Updater.ts` | updater (binary-only, SHA-256 hard gate) |

## Unmapped surface items

- **W8 (PR-risk scorer rubric)**: skill asset `builtin-skills/pr-risk-assessment/SKILL.md` was not recovered (gate ledger H3); only kill-switch and experiment wiring are characterized.
- **Agent Readiness Droid ([§3.4](../../prompts/droid.md#34-agent-readiness-droid-auditor-persona-head--associated-flows))**: auditor persona recovered; its `daemon.sf.*` readiness endpoints are partially mapped in CONFIG §6 — full readiness lifecycle not traced end to end.
- **W13 Agent Effectiveness report tools** (`get_agent_effectiveness_usage`, `render_agent_effectiveness_report`): prompt recovered; tool implementations not traced.
