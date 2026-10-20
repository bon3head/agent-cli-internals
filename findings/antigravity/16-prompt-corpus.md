# 16. The prompt corpus: personas are templates, and a Teamwork swarm ships inside

**Version pin:** agy v1.3.1, sha256 `085f43e0…455ef`.
**Full texts:** [prompts/antigravity.md](../../prompts/antigravity.md) (50 items, copied verbatim).

## 1. WHAT WAS FOUND

50 distinct prompts sit in the binary's prompt cluster (offsets ~91.6M–95.5M). Three facts matter most:

- **Personas are runtime-assembled, not stored.** The Antigravity Agent and Cascade texts survive only as Go template fragments (`{{.VerdictAccept}}`, `{{slot}}` markers, sentence shards). The binary never holds a finished system prompt; it stitches one at runtime from a pair-programming main block, identity lines, and mode blocks (including a NON-INTERACTIVE block). Two legacy personas ship side by side: "Antigravity Agent" and Codeium's "Cascade", same main block underneath.
- **A hidden multi-agent family: Teamwork.** Full prompt set for a swarm that coordinates through a shared blackboard file: `implementer@swe_light`, `reviewer@swe_light`, `qa@swe_light` role agents, a `swarm_follower`, a `blackboard_manager`, a `pipeline_blackboard_updater`, a `swarm_synthesizer`, and a Critic Orchestrator with mandatory spawn counts and an escalation ladder. Workspace paths in the text point at a `google3` root and `.agents/teamwork/` directories. This is separate from the coordinator/subagent prompts (routing coordinator, pipeline coordinator, research subagent, browser subagent), which also ship in full.
- **Two safety judges, full text.** The Jetski safety and security rater (offset 93322367, 1,549 chars) rates static snapshots of another agent's trajectory against an injected rubric. The command safety adjudicator (offset 95102230, 14,798 chars) is the longest contiguous prompt extracted from any of the four tools: it decides, per shell command, whether the command may run automatically (`reversible=true`) or needs a human (`reversible=false`). Finding 02 mapped the pipeline; this is the judge's actual decision text.

Also in the corpus: a code-review subagent prompt (/review-agent, read-only boundary, defect taxonomy), a tool-call error corrector, a sandboxed background helper, a search-engine bot, and utility prompts (title generator, worktree name, commit message).

## 2. HOW IT WAS FOUND

Printable-run extraction over the prompt cluster (min run 300 chars), scored and deduplicated, then assembled per category with offsets recorded per item. Template placeholders render as `{{slot}}` in the corpus copy.

## 3. WHAT IT UNLOCKS

Antigravity's behavior is configurable text all the way down: personas, subagent roles, and both safety judges are readable in full. The Teamwork set shows Google ships a second, blackboard-based swarm architecture next to the coordinator model, undocumented. And because personas are templates, the same binary can present different agents depending on which fragments the runtime selects.

## 4. HOW A DEVELOPER BUILDS ON IT

- Read the command safety adjudicator before tuning sandbox policy: its reversible/irreversible line is the rule your commands are judged by.
- Use the Teamwork role prompts as a spec: blackboard file, role split, synthesizer, critic. The pattern is implementable without Google's runtime.
- When diffing agy versions, diff fragments, not assembled prompts: fragment changes are the real changelog.
