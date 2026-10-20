# 17. The prompt corpus: no single system prompt, just style preambles plus shared sections

**Version pin:** claude 2.1.287, 244,317,368 bytes, Bun bundle.
**Full texts:** [prompts/claude-code.md](../../prompts/claude-code.md) (35 items, copied verbatim).

## 1. WHAT WAS FOUND

There is no contiguous main system prompt in the binary. The preamble exists in three style variants at three offsets: Proactive (offset 98158416), Concise (98158740), Explanatory (98159024). The rest of the system prompt is shared sections pulled in elsewhere: a Git Safety Protocol fragment, a pull-request fragment, an output-style block ("Writing for the user"). The prompt the model actually runs on is assembled from a style preamble plus shared sections, and which preamble ships may depend on user settings.

The corpus holds 35 items:

- **Built-in agents (7).** Plan (software architect, planning specialist), Explore (file search specialist), a general-purpose agent, and three review agents: a full 10,709-char security review prompt (senior security engineer, branch-diff review with output format and defect taxonomy), a review-for-recall prompt, and a review-for-precision prompt. Plus a batch orchestrator for parallel workers.
- **Feature agents (10).** Memory extraction and memory selection, workflow-script agents (their full final-answer contract), agent teams (teammate communication and coordination), compaction summary prompts with full instructions, the /design command handler, worktree session prompts, a comment-acknowledgement agent, and an auto-mode classifier rules reviewer.
- **Tool-internal prompts.** A web search assistant prompt, date/time parser, settings/hooks reference docs (the full hooks schema documentation), and **Claude in Chrome**: a browser-automation prompt with tool names (`mcp__claude-in-chrome__*`), GIF recording, and console-log filtering rules. A separate browser surface with its own instruction pack.
- **Tool descriptions (§5).** The embedded tool reference covers the standard set (Todo, Task, etc.) with when-to-use guidance.

## 2. HOW IT WAS FOUND

The bundle from finding 01 was searched for prompt starts (persona phrases, agent definitions) with ±context extraction; 38 scored runs trimmed to 35 items, each with its source offset. The three preambles sit within 600 bytes of each other, which is how the fragmented structure was confirmed.

## 3. WHAT IT UNLOCKS

Anyone who wanted "the Claude Code system prompt" was looking for something that does not exist. What exists is a prompt construction kit: three style preambles, shared protocol sections, and a full agent library whose review prompts are production-grade audit scripts. The security review prompt alone is a complete vulnerability-review protocol you can reuse.

## 4. HOW A DEVELOPER BUILDS ON IT

- Point your audit at the assembly, not the preamble: which style preamble is active changes the tone; the protocol sections do the work.
- Steal the security review prompt's structure for your own review bots (scope resolution, defect taxonomy, signal-to-noise bar).
- If you ship tooling that reads Claude Code's prompts, re-extract on version bump: the fragment list moves.
