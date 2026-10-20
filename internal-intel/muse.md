# Internal intel — Muse Code CLI (muse-bin-1.4.7-R6101.1)

**CONFIRMED** = byte-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

First pass on this target (2026-10-20): prompt corpus only. No control plane, telemetry, or auth pass yet.

## Prompt system (CONFIRMED)

- **Main prompt ships in two editions:** a shorter edition (~26K chars) and a tool-heavy edition (~45K chars), same section skeleton (Communication, Behavior, Verification), the heavy edition expanding tool and verification guidance. Which edition a session gets is not decided by anything in the prompt region. Full texts: [finding 01](../findings/muse/01-prompt-corpus.md), [prompts/muse.md](../prompts/muse.md).
- **Identity is a slot.** The prompt carries `{{model_identity}}`; the binary ships three identity blocks: Muse Spark, Muse Glimmer, generic Muse family.
- **The string table is duplicated:** a second full copy sits around offset +2.2M. Extractions must dedupe or every count doubles.
- **Bundled skill, not hidden machinery:** session storage ships as the full "Read Session" skill text (finding and restoring sessions, first-party commands).
- **No dedicated safety prompt.** Safety rules live in the main prompt's Behavior/Truthfulness section (including a ban on seeking hidden graders, oracles, or answer keys) and in a scope-reminder prompt. Contrast: codex and agy both ship separate judge prompts.
- **Lifecycle prompts:** goal reminder and scope reminder (both framed as "you are NOT the agent doing the task"), Herdr-pane prompt, context-compaction continuation, feature-tip picker.
- **Adjacent surfaces in the same cluster:** a computer-use assistant prompt and code-mode instructions next to a built-in tool inventory (native-basic profile).

## INFERENCE (gaps named)

- Two-edition selection rule (plan, surface, or model driven) unverified.
- Whether the duplicated string table is a second embedded copy or a build artifact of the packer.
