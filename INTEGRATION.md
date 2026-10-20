# Integration synthesis: what five agent CLIs are actually built like

Five binaries, five vendors, one pattern nobody advertised. Each CLI ships a platform,
not a chat box: a permission engine, a consent pipeline, a kill-switchable updater, a
bundled skill corpus, and a prompt construction kit. This doc states what separates the
five tools, what they share, and what makes each one's internals novel relative to the
features it sells. Every claim links to the doc that proves it. The [method appendix](#method-appendix-how-the-maps-were-made)
explains how each map was produced and why you can audit it.

## 1. What separates the five tools

**codex (OpenAI, Rust): policy by slot, judge by Guardian.** Codex's Security Policy is not
in the binary: it is a runtime-injected template (`{{tenant_policy_config}}`), so policy
updates need no release. The action gate is the Guardian: a full action-review prompt that
judges every planned tool call ([prompts/codex.md#21-guardian-action-review-prompt-you-are-judging-one-planned-coding-agent-action](prompts/codex.md#21-guardian-action-review-prompt-you-are-judging-one-planned-coding-agent-action)).
The binary also documents its own protocol: one subcommand prints all 102 client-to-server
methods as JSON Schema ([findings/codex/01-app-server-protocol.md](findings/codex/01-app-server-protocol.md)).
The tell is the updater: it fetches a shell script and runs `/bin/sh -s`, the only tool
of the five whose update path is script-execution instead of a signed blob
([findings/codex/15-gated-rerun.md](findings/codex/15-gated-rerun.md)).

**antigravity (Google, Go): the swarm ships inside.** Antigravity is the only tool whose
persona never exists as text: it is stitched at runtime from Go template fragments, with
two legacy personas (Antigravity Agent, Codeium Cascade) on the same main block. And it
ships a second, undocumented multi-agent architecture: the Teamwork family coordinates
through a shared blackboard file (implementer/reviewer/qa agents, a blackboard manager,
a swarm synthesizer, a Critic Orchestrator) next to the ordinary coordinator model
([findings/antigravity/16-prompt-corpus.md](findings/antigravity/16-prompt-corpus.md)).
Its command safety adjudicator is the longest contiguous prompt extracted from any tool
(14.8K chars), and its local control plane is 348 RPC methods on `localhost:5387`
drivable with curl ([findings/antigravity/13-rpc-service-map.md](findings/antigravity/13-rpc-service-map.md)).

**claude-code (Anthropic, Bun): there is no main prompt to leak.** The binary stores no
contiguous system prompt, only three style preambles and shared sections that get assembled
at runtime. The as-served capture proved why: the real prompt is compact (~6K chars) and
most behavior text lives in tool descriptions, served not stored
([findings/claude-code/17-prompt-corpus.md](findings/claude-code/17-prompt-corpus.md)).
Its permission engine is the most precisely decoded of the five: deny > ask > allow >
passthrough, first-match, byte-confirmed in the minified bundle, including the trap that
`Write(path)` rules are never matched ([findings/claude-code/03-permission-engine.md](findings/claude-code/03-permission-engine.md)).

**muse (Meta): two editions, no judge.** Muse's main prompt ships in two editions (26K
and 45K chars) with an identity placeholder the runtime fills (Spark, Glimmer, or generic),
and it is the only tool with no dedicated safety prompt at all: safety rules live inside
the main prompt's Behavior section ([findings/muse/01-prompt-corpus.md](findings/muse/01-prompt-corpus.md)).
The oddity is the bundled Read Session skill: session recovery is published as a skill
the agent reads, not hidden machinery.

**droid (Factory, Bun): it judges you.** Droid is the only tool with a hidden analytics
judge pipeline: one persona, three rubrics, one of which scores the *user's* expertise
from session transcripts on triggers the user cannot see, behind an org-controlled
consent gate ([findings/droid/04-judges-and-localsignals.md](findings/droid/04-judges-and-localsignals.md)).
Per turn, a real LLM classifier (Alloy) picks the model from 9 scored capability cards,
cheapest at or above 0.7 ([findings/droid/05-alloy-router.md](findings/droid/05-alloy-router.md)).
Its safety story is also the strangest: a three-layer learned Shield that runs for real,
next to a second independent risk classifier deliberately kept in shadow mode by written
contract ([findings/droid/10-safety-machinery.md](findings/droid/10-safety-machinery.md)).
And the binary shipped 50.5 MB of its own original source, so this map was re-gated
against Factory's own code ([findings/droid/03-source-recovery-method.md](findings/droid/03-source-recovery-method.md)).

## 2. What they share

The five vendors converged on the same machine, independently:

- **Telemetry is a pipeline, not a flag.** Every tool ships multiple channels (Sentry DSN
in codex, droid, claude's Datadog; OTel legs; per-turn cost and event endpoints). The
off-switch, where it exists, is qualified: droid's `telemetry.enabled: false` works but
the org can force it back on and Sentry has no switch; agy's usage stats have no CLI
kill switch; codex's OTel has no opt-out literal.
- **Permission is a confirmation layer, not an access-control layer.** Claude's
deny/ask/allow, droid's confirmation layer (which `--skip-permissions-unsafe` disables,
leaving blocklists, policy preflight, and hooks still firing), agy's per-step safety
screen: all three are graded ladders with a hard block class above the top tier.
- **Updates are kill-switchable.** Signed and checksum-gated binaries (claude RSA-4096,
droid SHA-256), a master kill switch (claude), Cloud Run as the real host (agy), and
codex's script-piped updater, the outlier.
- **Prompts are constructed, not written.** Go templates (agy), style preambles plus
shared sections (claude), dual editions (muse), a runtime policy slot (codex), per-turn
classifier context (droid). The static "system prompt" is a fossil in every case.
- **Skills and agents are bundled corpora.** Ten-plus skill families ship as text in the
binary (agy's embedded docs are byte-identical to the runtime corpus; droid's dogfood
skill is the vendor's internal QA workflow handed to every user; claude's review
prompts are production-grade audit scripts).
- **Hooks are the contract surface.** Pre/post tool hooks with typed event schemas appear
in agy (6 events), claude (33), and droid (PreToolUse allow/deny/ask), each with the
same precedence rule: block beats ask beats allow.
- **Experiments are vendor machinery.** GrowthBook (claude), Statsig (droid), Unleash
(agy): remote flag systems that can change tool behavior without a release, and the
model registries draw the public/internal line (Mythos internal-only vs Fable public;
GPT-6 Astra Work-only).

## 3. Unique novel internals, feature by feature

- **codex:** the `instructions_template` for gpt-6-astra ships byte-exact in a CLI binary
  even though that model is Work-surface-only; the app-server schema subcommand turns
  protocol documentation into a self-describing CLI; the per-turn cost endpoint plus
  `line_fingerprints`/`repo_hash` in `codex_turn_event` make every turn meterable to the
  line ([findings/codex/08-telemetry.md](findings/codex/08-telemetry.md)).
- **antigravity:** the 164,366-function Go table was cracked without a disassembler
  (2.9s, under 100MB RAM) after a toolchain anomaly in the pclntab header was brute-forced
  through 30 layout combos; the `--disable_telemetry` flag claim died to a control
  experiment and is preserved as a kill, not deleted
  ([methodology/README.md](methodology/README.md)).
- **claude-code:** the served prompt was captured by pointing the real CLI at a logging
  stub with canned responses, proving the "classic long prompt" folklore is a pre-2.1.287
  artifact; the permission engine's rule-validator strings read like a linter spec, and
  the repo-controllable guard makes `bypassPermissions` ungrantable from project settings
  ([findings/claude-code/03-permission-engine.md](findings/claude-code/03-permission-engine.md)).
- **muse:** safety-by-section rather than safety-by-judge is a real architectural choice
  visible in the prompt layout, and the main prompt carries an explicit ban on hunting
  for hidden graders or answer keys, a meta-instruction none of the other four ship.
- **droid:** the surface-to-internals [crosswalk](findings/droid/crosswalk.md) ties every
  front-facing feature (autonomy tiers, `--skip-permissions-unsafe`, Shield, Mission
  mode, ExitCourier, stats badges, hidden `dataset`/`experiments` entrypoints) to its
  prompt section and its source module, including the three rows left honestly unmapped;
  the bespoke V8-isolate script engine backs the agent-visible `Script` tool behind an
  "Unsafe Script" binding; act-as grants are backend-minted with 5-minute TTLs and the
  CLI never mints them, the opposite of what string evidence first suggested
  ([findings/droid/07-script-engine-and-agent-browser.md](findings/droid/07-script-engine-and-agent-browser.md)).

## Method appendix: how the maps were made

Every claim in this repo is traceable to frozen bytes and a named method. The three
toolchains needed three instruments: Go pclntab parsing for agy, Bun string-table
carving for claude and droid, and Rust serde-`FIELDS` statics plus the binary's own
schema-generator subcommands for codex ([methodology/README.md](methodology/README.md)).
A systemic lesson from the reinforcement pass: packed-string-run tokenizing is a lossy
counting method and caused every major count error in the first pass; the repo now flags
which counts come from exact methods and which remain lossy.

Rigor machinery per tool:

- **codex:** the `local-re-swarm` skill ran a gated rerun: 188 prior claims plus 38 new
  lane claims were gated by a fresh verifier context against the re-pinned bytes
  (exact-equality, never grep line counts), producing 80/40/45/23 and 32/3/3/0 verdict
  splits with dated corrections kept in place
  ([findings/codex/15-gated-rerun.md](findings/codex/15-gated-rerun.md)).
- **claude-code:** the as-served capture ran the real CLI against a local logging proxy
  (auth redacted at capture, proxy killed after) and the served tool catalog's 30
  descriptions recovered what static carving could not
  ([findings/claude-code/17-prompt-corpus.md](findings/claude-code/17-prompt-corpus.md)).
- **antigravity:** control experiments kill what assertion cannot: the
  `--disable_telemetry` refutation is in the record as a deliberate negative
  ([methodology/README.md](methodology/README.md)).
- **droid:** four lanes, two silo gap-audits by fresh rotated auditors trying to break
  claims, three brute-force waves, a local-stub dynamic capture, then source recovery:
  the Bun module-graph record store yielded 50.5 MB of original unminified source
  (4,999 zstd frames; the two wrong turns and the exact method are in
  [findings/droid/03-source-recovery-method.md](findings/droid/03-source-recovery-method.md)).
  All lane claims were then re-gated source-first (64 clusters), followed by an
  association audit (57/57 modules verified against the binary), a module-coverage
  census (83.2% covered, every uncovered module read), and a source-execution proof
  (5,484/5,484 parse, 22/22 functional cases, rubric output found byte-for-byte in the
  binary). The surface-to-internals crosswalk is the integration artifact
  ([findings/droid/crosswalk.md](findings/droid/crosswalk.md)).
- **muse:** prompt-corpus pass only; no dynamic capture and no gated rerun were run,
  stated as the honest boundary ([findings/muse/01-prompt-corpus.md](findings/muse/01-prompt-corpus.md)).

Failures stay in the record: wrong first writeups (claude's gateway), refuted claims
(agy's telemetry flag), method artifacts (droid's protobuf label, the zstd kill), and
partial trials are marked as such rather than smoothed over. Dated errata correct in
place; originals stand. The [eureka log](eureka-log.md) carries the chronological
discovery record and its hash chain.
