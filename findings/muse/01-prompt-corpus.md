# 01. Muse Code: the main prompt ships in two editions, no dedicated safety prompt

**Version pin:** muse-bin-1.4.7-R6101.1, 363,518,168 bytes (`~/.local/bin/muse-bin-1.4.7-R6101.1`).
**Full texts:** [prompts/muse.md](../../prompts/muse.md) (16 items, copied verbatim).

## 1. WHAT WAS FOUND

16 prompt items extracted from the binary's packed string table (offsets ~0.5M–8M):

- **The main prompt ships in two editions.** The Muse Code system prompt appears in a shorter edition (~26K chars) and a tool-heavy edition (~45K chars), with the same section skeleton (Communication, Behavior, Verification) expanded in the heavy one. The string table embeds more than once (a second full copy around offset +2.2M); duplicates are noted once.
- **Identity is a template.** The prompt carries a `{{model_identity}}` placeholder; the binary ships three identity blocks: Muse Spark, Muse Glimmer, and a generic Muse-family block. The same CLI can present as any of them.
- **A bundled "Read Session" skill.** Session storage is not just code: the binary ships the full Read Session skill text (finding and restoring sessions, first-party commands). Session management is a documented skill, not hidden machinery.
- **No dedicated safety prompt.** Nothing resembling a moderation/classifier system prompt was found in the prompt region. Safety-adjacent rules live inside the main prompt's Behavior/Truthfulness section (including an explicit ban on looking for hidden graders, oracles, or answer keys) and the scope-reminder text.
- **Lifecycle prompts.** Goal and scope reminders ("you are NOT the agent doing the task"), a Herdr-pane prompt, context-compaction continuation text, and a feature-tip picker. A computer-use assistant prompt and code-mode instructions ship adjacent to a built-in tool inventory (native-basic profile).

## 2. HOW IT WAS FOUND

Printable-run extraction over the binary's prompt region, scored for prompt-likeness, deduplicated across the string table's repeated copies, assembled per category with offsets per item.

## 3. WHAT IT UNLOCKS

The first byte-level look at Meta's coding CLI: its main instruction text in both editions, its identity system, and the session-recovery skill. And a contrast point against the other three tools: Meta puts safety rules inside the main prompt rather than in a separate judge.

## 4. HOW A DEVELOPER BUILDS ON IT

- Compare the two editions section by section to see what the tool-heavy variant adds (verification and tool guidance).
- The Read Session skill text is a working spec for session persistence and recovery.
- The goal/scope reminder pattern is a cheap prompt-engineering device for handoff and scope discipline.
