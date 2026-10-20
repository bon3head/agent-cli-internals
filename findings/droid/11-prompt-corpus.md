# 11. The prompt corpus: extraction method, coverage, honest negatives

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Full corpus: [prompts/droid.md](../../prompts/droid.md) (105,545 bytes, byte-identical to the
run extract).

## HOW IT WAS FOUND

1. **mmap anchor sweeps**: scored candidate prompt-runs by density of instruction phrasing;
   candidates preserved under `runs/droid/extracts/`.
2. **UTF-16LE sweeps**: the JSC string table stores non-Latin1 strings as UTF-16LE - ASCII-only
   sweeps missed entire clusters (the Alloy router prompt, 25 persona heads at 265.5–267.8M,
   the mission-validator family at 95.7–96.1M). Decoding both widths closed that.
3. **Source recovery** (finding 03) upgraded everything: claims re-gated against original source.

## COVERAGE

- Core personas: orchestrator, mission orchestrator, workers, harness/working-repos/
  communication fragments; autonomy tiers + `droid exec` help verbatim; spec mode; the
  Script tool; session-title generator; Agent Effectiveness skill; mission handoff schema.
- Safety: full Droid Shield trio, the operation-risk classifier (bundle-only, 5,918 chars),
  the analytics judges, agent readiness auditor, catastrophic tables.
- UTF-16 annexes: model-router classifier prompt, security-review mega-document (229,774 chars),
  Slack triage agent (16,122), severity rater, novelty reducer, PR-risk category scorer.

## HONEST NEGATIVES

- **Codex's Security Policy is a runtime slot** in its own tool; Droid has no equivalent
  injected-policy surface observed - no such slot found (searched, zero hits).
- **No "INTERNAL USE ONLY" markers** in the binary (honest negative: looked for, not found).
- No factory://, droid://, vscode:// URL schemes (swept, certified negative).
- PR-risk rubric `builtin-skills/pr-risk-assessment/SKILL.md` was **not recovered**; only
  kill-switch and experiment wiring are characterized.
- The `LlmProxyPath` enum's defining module has no record in the recovered module graph
  (values inlined at build; not a pairing error).

## CONFIRMED vs INFERENCE

Everything above is byte- or source-verified. What remains inference: whether the recovered
source is the exact commit behind the shipped build (5,484/5,484 modules parse, rubrics
generated from source match the binary byte-for-byte - strong but not a build hash).
