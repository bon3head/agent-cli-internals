# 05. Alloy: a per-turn LLM model router with 9 scored capability cards

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source. Full classifier prompt:
[prompts/droid.md §A.1](../../prompts/droid.md#a1-the-model-router-classifier-prompt-new--utf-16-only-absent-from-earlier-sections).

## WHAT WAS FOUND

**Alloy is Droid's model router** - an LLM classifier invoked per turn
(`packages/droid-core/src/model-router/factory-router-routing.ts:440-468`) with a
16k-token `<session>` context (current user message rendered last). Default model:
**gpt-5.4-mini**, ReasoningEffort.Low, 10s timeout. Selector: cheapest candidate scoring
≥ 0.7 (`selector.ts`); image-blind candidates are hard-zeroed on image turns.

Nine per-model capability cards with numeric eval-score anchors (`model-cards.ts`):
`OPUS_5_5`, `KIMI_K3`, `KIMI_K2_7_CODE`, `MINIMAX_M3`, `DEEPSEEK_V4_1_FLASH`, `GLM_5_3`,
`GPT_6_1_SOL`, `GPT_5_6_TERRA`, `GPT_6_LUNA`. Org routing guidance is **advisory only**:
"they do not override the scoring rubric, model capability cards, or policy constraints"
(`prompt.ts:73-77`).

The classifier prompt was stored **UTF-16LE-only in the binary** (no Latin-1 twin) - the
mechanism that hid it from ASCII string sweeps. Gate correction: that's a binary artifact;
the recovered source is plain UTF-8. The wire evidence agrees: as-served dynamic capture
showed `fallbacks: [{claude-opus-5}]` on the wire.

The model registry behind it is ~97.3M: gpt-6-astra, gpt-6.1-sol, gpt-6-luna, claude-opus-5-5,
claude-fable-5(.1), claude-mythos-preview, gemini-4-argon, grok-4.5/4.6/4.7, kimi-k3, plus
Fireworks/Together/Mistral/Baseten and Bedrock BYOK. A hardcoded OpenAI org id ships in the
binary (@97.301M).

## HOW IT WAS FOUND / WHAT IT UNLOCKS

BRUTE-MAX found the UTF-16LE-only cluster; the gate re-derived the routing logic from
`prompt.ts`, `selector.ts`, `context.ts`. A per-turn LLM router means your model choice is
a *suggestion* - the classifier spends your quota by its own rubric, and org admins can't
override the cards, only advise. The eval-score anchors in `model-cards.ts` are a leak of
Factory's internal model benchmarking.
