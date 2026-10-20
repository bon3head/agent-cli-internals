# 14. The full prompt corpus: every system prompt the binary ships

**Version pin:** codex 0.155.1, sha256 `0753dfe1…b761`, 269,273,536 bytes.
**Full texts:** [prompts/codex.md](../../prompts/codex.md) (34 items, copied verbatim).

## 1. WHAT WAS FOUND

Every prompt the CLI runs on is embedded as readable text in `.rodata`. The corpus has 34 items in five groups:

- **Core personas (7).** A general-purpose assistant prompt ("You are Codex, an OpenAI general-purpose agentic assistant"), the classic CLI coding prompt, two side-conversation variants, and per-model `instructions_template`s: one for `gpt-6-astra`, one for `gpt-5.6-sol`. Each model's template ships inside its catalog entry, so the prompt a model runs on is a per-model data field, not code.
- **Guardian & safety (7).** The Guardian action-review prompt ("You are judging one planned coding-agent action") with its risk taxonomy, the Guardian V2 classifier instructions, a Computer/Browser Use addendum, and the confirmation policy. The auto_review seat from finding 07/11 is this text.
- **The Security Policy is not in the binary.** Both Guardian prompts contain the literal slot `{{ tenant_policy_config }}` where the policy goes. The shipped binary carries the judge and the rubric structure; the policy text is injected at runtime. What the policy says on any given day is not recoverable from the binary.
- **Orchestration (9).** Delegation pack (spawn_agent instructions), collaboration-mode text, persistent-mode prompt, memory-consolidation fragment, context-window/compaction texts, a code-review prompt fragment.
- **Tool instructions (7+).** The `web.run` pack (usage hints, decision boundary, citations, word limits), `tool_search` description, unified-exec parameter descriptions, and an MCP approval-template table: 55 templates (parameter names captured for the first 17 in-window; the rest carry verified title + template).

One loss: the code-mode `declare const tools:` body is placeholder-substituted in the packed literals, so the full tool list with signatures is not recoverable from strings. Fragments only (finding 12 covers the 14 injected names by another route).

## 2. HOW IT WAS FOUND

Bounded `mmap` anchor scans on the frozen binary: persona anchors (`You are Codex`, `Security Policy`, `classifier_instructions`, `policy_template`) cluster at file offsets 217M–224M. Windows around each anchor were extracted, escapes decoded, and each prompt trimmed to its real boundaries. The method lists came from the schema bundle already emitted by finding 01's generator run.

## 3. WHAT IT UNLOCKS

You can read the exact instructions the agent works under, per model, before you ever run it. That includes the safety judge's rubric and the one thing you cannot read: the Security Policy, which OpenAI can change server-side without shipping a new binary.

## 4. HOW A DEVELOPER BUILDS ON IT

- Diff the persona templates across model entries to predict behavior differences between models on the same task.
- Read the Guardian prompts before designing approval workflows: the risk taxonomy is the decision procedure, in full.
- Treat `{{ tenant_policy_config }}` as a runtime input: log it if your host injects it, and never assume the binary's copy (there is none).
- Re-derive with anchor scans after any version bump; offsets move, the anchor phrases are stable.
