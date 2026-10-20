# agent-cli-internals

**Your AI coding tools look like chat boxes. Underneath, they're platforms with hidden control panels. This repo documents the panels.**

Five CLIs were taken apart byte by byte: Google's `agy` (Antigravity), Anthropic's `claude` (Claude Code), OpenAI's `codex`, Meta's `muse` (Muse Code, prompts pass only), and Factory's `droid` (Factory Droid, first public map of the binary). No live model call was made and no real request left the box. Everything here comes from the text baked into the programs, the settings they ship with, and the self-describing specs some of them carry. (2026-10-20: Claude Code's served prompts were additionally captured by running the CLI against a local stub endpoint returning canned responses; that material is marked "as served". Droid was additionally run in a sandbox HOME against a local loopback stub, strace-verified, for its as-served capture; Droid's own module-graph record store yielded 50.5 MB of its original unminified source, which the full pass was then re-gated against.)

**Versions:** `agy` v1.3.1 · `claude` 2.1.287 · `codex` 0.155.1 · `muse` 1.4.7 · `droid` v0.245.0
**Also here:** [methodology](methodology/README.md) · [eureka log](eureka-log.md) · [PoCs](pocs/) · [diagrams](diagrams/) · [full prompt texts](prompts/) · [honesty box](#honesty-box) (caveats and what was not verified)

## Start here: the influential bits

- [Integration synthesis: what five agent CLIs are actually built like](INTEGRATION.md) (what separates them, what they share, feature-to-mechanism mappings, the audit methods)
- [The binary ships its own source: 50.5 MB of original Droid modules recovered from the Bun module graph](findings/droid/03-source-recovery-method.md) (the extraction method, including the two wrong turns)
- [Factory-Judge: one persona, three rubrics, and it scores the user](findings/droid/04-judges-and-localsignals.md) ("Judge the user, not the assistant"; org-controlled consent gate)
- [Droid prompt corpus](prompts/droid.md#3-safety--security) (Shield triage, the shadow risk classifier, analytics judges; full two-level index in [prompts/](prompts/README.md))
- [Surface ↔ internals crosswalk: read the agent's mind at any moment](findings/droid/crosswalk.md) (every front-facing droid feature mapped 1-1 to its prompt section + mechanism, hyperlinked both ways)
- [gpt-6-astra `instructions_template`](prompts/codex.md#13-you-are-codex-an-agent-based-on-gpt-6-gpt-6-astra-instructions_template) (gpt-6-astra's full system prompt, byte-exact)
- [Guardian action-review prompt](prompts/codex.md#21-guardian-action-review-prompt-you-are-judging-one-planned-coding-agent-action) (the judge that approves codex tool calls)
- [Security Policy template](prompts/codex.md#23-security-policy-template) (codex's security policy is injected, not embedded)
- [Muse Code main prompt, both editions](prompts/muse.md#1-core-personas) (muse's main prompt, both shipped editions)
- [Bundled "Read Session" skill](prompts/muse.md#21-session-storage--bundled-read-session-skill-offset-2321100-the-storage-statement-itself-at-2321273) (bundled skill that reads your past sessions)
- [Claude Code served system prompt](prompts/claude-code.md#0-as-served-dynamic-capture-2026-10-20) (compact ~6K prompt captured live; the binary itself stores only fragments)
- [Security review agent](prompts/claude-code.md#24-security-review-agent-offset-98276396) (claude code's complete security-review protocol)
- [Jetski safety and security rater](prompts/antigravity.md#jetski-safety-and-security-rater) (the safety judge screening agy actions)
- [Command safety adjudicator](prompts/antigravity.md#command-safety-adjudicator) (decides if a shell command is reversible)
- [Teamwork agent: implementer + QA roles](prompts/antigravity.md#teamwork-agent-implementer--qa-roles) (undocumented multi-agent swarm inside agy)
- [Telemetry addendum (2026-10-20)](findings/codex/08-telemetry.md#addendum-2026-10-20-gated-rerun-all-verified-against-frozen-bytes) (sentry dsn, cost endpoint, code fingerprints)
- [Updater note (internal intel)](internal-intel/codex.md#prompt-corpus--gated-rerun-2026-10-20-confirmed) (standalone updater runs a fetched shell script)

## Contents

This page: [start here](#start-here-the-influential-bits)
- [The 30-second version](#the-30-second-version)
- [The three control planes at a glance](#the-three-control-planes-at-a-glance)
- [What this unlocks (in plain English)](#what-this-unlocks-in-plain-english)
- [Receipts: cracked open, on the record](#receipts-cracked-open-on-the-record)
- [Findings index, ranked by bigness](#findings-index-ranked-by-bigness)
- [For developers](#for-developers)
- [Honesty box](#honesty-box)

Tools and their internals:

- **agy (Google Antigravity)** · [prompts](prompts/antigravity.md) · [internal intel](internal-intel/antigravity.md) · findings:
  - [01. Local control plane: the language server is a fully drivable agent socket](findings/antigravity/01-local-control-plane.md)
  - [02. Safety screen decoded: per-step, 2-stage, server-overridable](findings/antigravity/02-safety-screen.md)
  - [03. Model catalog: server-driven, 4-tier waterfall, 39-entry alias map](findings/antigravity/03-model-catalog.md)
  - [04. Auth = Gemini Code Assist machinery; device flow + PKCE, 3 client IDs](findings/antigravity/04-auth.md)
  - [05. Telemetry: three pipelines; usage stats have no CLI kill switch](findings/antigravity/05-telemetry.md)
  - [06. Sidecar web server: token-authenticated local HTTP agent handle](findings/antigravity/06-sidecar-server.md)
  - [07. Full hook contract extracted (6 events, protojson stdin/stdout)](findings/antigravity/07-hook-contract.md)
  - [08. Embedded docs ARE the runtime skill corpus (10/12 byte-identical on disk)](findings/antigravity/08-embedded-skill-corpus.md)
  - [09. pclntab cracked: 164,366 functions enumerated in 2.9s, <100MB RAM](findings/antigravity/09-pclntab.md)
  - [10. Remote-control mesh + mic-serve + sandbox IPC mapped](findings/antigravity/10-remote-mesh.md)
  - [11. Internal intel overview: lineage, codenames, kill switches, update mechanics](findings/antigravity/11-internal-intel-overview.md)
  - [12. BYO model path: `AGY_LLM_GATEWAY_*` env vars](findings/antigravity/12-byo-model-path.md)
  - [13. The 889-method RPC service map](findings/antigravity/13-rpc-service-map.md)
  - [14. Unleash: the second flag system](findings/antigravity/14-unleash-flag-system.md)
  - [15. Cloud Run auto-updater: the real update host](findings/antigravity/15-cloud-run-updater.md)
  - [16. The prompt corpus: personas are templates, and a Teamwork swarm ships inside](findings/antigravity/16-prompt-corpus.md)
- **claude (Claude Code)** · [prompts](prompts/claude-code.md) · [internal intel](internal-intel/claude-code.md) · findings:
  - [01. Full JS bundle carved from the binary (C6)](findings/claude-code/01-bundle-surgery.md)
  - [02. Settings schema fully recovered: 183 typed keys (C1)](findings/claude-code/02-settings-schema.md)
  - [03. Permission decision engine decoded (C1)](findings/claude-code/03-permission-engine.md)
  - [04. 33 hook events, 5 hook types (C1)](findings/claude-code/04-hook-events.md)
  - [05. Cloud-session control plane mapped (C2)](findings/claude-code/05-cloud-control-plane.md)
  - [06. `claude gateway` is a full HTTP server in the binary (C2)](findings/claude-code/06-gateway-server.md)
  - [07. MCP: CLI serves itself; first-party endpoints expanded (C3)](findings/claude-code/07-mcp-plane.md)
  - [08. Plugin plane: marketplace = GCS + git, sha256-pinned trust (C3)](findings/claude-code/08-plugin-plane.md)
  - [09. Auth plane: endpoints, client IDs, storage, providers (C4)](findings/claude-code/09-auth-plane.md)
  - [10. Model families in the binary: Fable 5/5.1 (public) and Mythos 5/5.1 (internal-only) (C5)](findings/claude-code/10-fable-mythos.md)
  - [11. Codenamed experiment gates + grounded feature families (C5)](findings/claude-code/11-experiment-gates.md)
  - [12. Hidden flags and aliases (C2/C3)](findings/claude-code/12-hidden-flags.md)
  - [13. GrowthBook is the experiment SDK (NOT Statsig)](findings/claude-code/13-growthbook-experiment-sdk.md)
  - [14. Hidden commands + unregistered `claude daemon` + child-session flag forwarding](findings/claude-code/14-hidden-commands.md)
  - [15. Gateway full route table (18 paths)](findings/claude-code/15-gateway-route-table.md)
  - [16. Update signing (RSA-4096), Datadog sink, event logging, master kill switch](findings/claude-code/16-update-signing-datadog.md)
  - [17. The prompt corpus: no single system prompt, just style preambles plus shared sections](findings/claude-code/17-prompt-corpus.md)
- **codex (OpenAI Codex CLI)** · [prompts](prompts/codex.md) · [internal intel](internal-intel/codex.md) · findings:
  - [01. The binary ships its own app-server protocol spec](findings/codex/01-app-server-protocol.md)
  - [02. Wire-envelope quirks that break naive JSON-RPC clients](findings/codex/02-wire-quirks.md)
  - [03. Transports: stdio, unix socket, websocket](findings/codex/03-transports.md)
  - [04. codex-code-mode-host: Rust+V8 cell executor over gRPC or stdio IPC](findings/codex/04-code-mode-host.md)
  - [05. Config: 101 of 101 fields recovered, 10-layer precedence](findings/codex/05-config-surface.md)
  - [06. Auth: five login types; session-level, not per-method](findings/codex/06-auth.md)
  - [07. Rate limits are readable AND redeemable](findings/codex/07-rate-limits.md)
  - [08. Telemetry is three channels, not one](findings/codex/08-telemetry.md)
  - [09. MCP is a first-class citizen with a future protocol version negotiated in-code](findings/codex/09-mcp.md)
  - [10. `codex cloud` is experimental-tagged but fully present](findings/codex/10-codex-cloud.md)
  - [11. The autonomy roadmap is a config surface: six experimental structs, fully field-recovered](findings/codex/11-roadmap-struct-fields.md)
  - [12. The code-mode sandbox is exactly 14 injected names (and no more)](findings/codex/12-cell-globals.md)
  - [13. The 0.149.0 → 0.155.1 feature-flag delta + the hidden `--managed-daemon` flag](findings/codex/13-flag-delta-managed-daemon.md)
  - [14. The full prompt corpus: every system prompt the binary ships](findings/codex/14-prompt-corpus.md)
  - [15. Gated rerun: an independent verifier re-checked 226 claims against the frozen bytes](findings/codex/15-gated-rerun.md)
- **droid (Factory Droid)** · [prompts](prompts/droid.md) · [internal intel](internal-intel/droid.md) · findings:
  - [01. Config and permissions: 251 envs, the real flag semantics, 167 daemon RPCs, hidden internal tooling](findings/droid/01-config-and-permissions.md)
  - [02. Telemetry and Sentry: the kill switch exists, the org can override it, Sentry cannot be turned off](findings/droid/02-telemetry.md)
  - [03. The binary ships its own source tree: Bun module-graph records, 4,999 zstd frames, 43.5 MB](findings/droid/03-source-recovery-method.md)
  - [04. Factory-Judge: one persona, three rubrics, including a judge that scores the user](findings/droid/04-judges-and-localsignals.md)
  - [05. Alloy: a per-turn LLM model router with 9 scored capability cards](findings/droid/05-alloy-router.md)
  - [06. Protocol and auth: LLM gateway, device-code OAuth, keyring, and the session store](findings/droid/06-protocol-and-auth.md)
  - [07. The script engine, the agent browser, and the internal QA skill everyone got](findings/droid/07-script-engine-and-agent-browser.md)
  - [08. The registries: 317 flags, 109 cost blocks, 251 envs, 61 paths, 167 daemon methods](findings/droid/08-registries.md)
  - [09. As served: the dynamic capture (4,844-char exec prompt, 10 vs 11 tools, wire fallbacks)](findings/droid/09-as-served-capture.md)
  - [10. Safety machinery: Droid Shield's three layers and the shadow risk classifier](findings/droid/10-safety-machinery.md)
  - [11. The prompt corpus: extraction method, coverage, honest negatives](findings/droid/11-prompt-corpus.md)
  - [Crosswalk: surface ↔ internals, every feature mapped 1-1 to prompt + mechanism](findings/droid/crosswalk.md)
- **muse (Meta Muse Code)** · [prompts](prompts/muse.md) · [internal intel](internal-intel/muse.md) · findings:
  - [01. Muse Code: the main prompt ships in two editions, no dedicated safety prompt](findings/muse/01-prompt-corpus.md)

Prompt corpora with their internal category sections:
- [codex](prompts/codex.md): [Conventions](prompts/codex.md#conventions), [1. Core personas](prompts/codex.md#1-core-personas), [2. Guardian & safety](prompts/codex.md#2-guardian--safety), [3. Orchestration prompts](prompts/codex.md#3-orchestration-prompts), [4. Tool instructions & declarations](prompts/codex.md#4-tool-instructions--declarations), [5. App-server protocol methods by namespace](prompts/codex.md#5-app-server-protocol-methods-by-namespace), [Item inventory](prompts/codex.md#item-inventory)
- [antigravity](prompts/antigravity.md): [1. Core personas](prompts/antigravity.md#1-core-personas), [2. Subagents & orchestration](prompts/antigravity.md#2-subagents--orchestration), [3. Safety & policy](prompts/antigravity.md#3-safety--policy), [4. Utility prompts](prompts/antigravity.md#4-utility-prompts), [5. Tool-related text](prompts/antigravity.md#5-tool-related-text)
- [claude-code](prompts/claude-code.md): [0. As served (dynamic capture)](prompts/claude-code.md#0-as-served-dynamic-capture-2026-10-20), [1. Core system prompt](prompts/claude-code.md#1-core-system-prompt), [2. Built-in agents](prompts/claude-code.md#2-built-in-agents), [3. Feature & workflow agents](prompts/claude-code.md#3-feature--workflow-agents), [4. Tool-internal prompts](prompts/claude-code.md#4-tool-internal-prompts), [5. Tool descriptions](prompts/claude-code.md#5-tool-descriptions)
- [muse](prompts/muse.md): [1. Core personas](prompts/muse.md#1-core-personas), [2. Session & lifecycle](prompts/muse.md#2-session--lifecycle), [3. Safety & policy](prompts/muse.md#3-safety--policy), [4. Tool-related text](prompts/muse.md#4-tool-related-text), [5. Other agent modes](prompts/muse.md#5-other-agent-modes)
- [droid](prompts/droid.md): [1. Core personas](prompts/droid.md#1-core-personas), [2. Autonomy tiers (PRIORITY SECTION)](prompts/droid.md#2-autonomy-tiers-priority-section), [3. Safety & security](prompts/droid.md#3-safety--security), [4. Subagents & utilities](prompts/droid.md#4-subagents--utilities), [5. Tool-related text](prompts/droid.md#5-tool-related-text), [Annex A: model-router classifier + UTF-16 census](prompts/droid.md#annex-brute2-2026-10-20-the-model-router-classifier-utf-16-corpus-twin-checks), [Annex B: UTF-16LE skill-asset cluster](prompts/droid.md#annex-b-closure-wave-2026-10-20-the-utf-16le-skill-asset-cluster-265525259267817190), [Gate errata + annex](prompts/droid.md#gate-errata--annex-source-recovery-2026-10-20)

More: [methodology](methodology/README.md) · [eureka log](eureka-log.md) · [diagrams](diagrams/) · [PoCs](pocs/)

## The 30-second version

- **Antigravity exposes 889 RPC methods across 30 services**, including a 348-method local control server (`localhost:5387`) you can drive with curl. The binary prints the recipe.
- **Codex documents its own protocol.** One built-in command prints all 102 client-to-server API methods as JSON Schema.
- **Claude Code's 41MB app was carved out as readable JavaScript.** Permissions, settings, and cloud features are all searchable text now.
- **The binaries draw the public-vs-internal line themselves.** Mythos 5/5.1 is the internal-only model family; Fable 5/5.1 and GPT-6 Astra are public.
- **Every system prompt ships in the binary.** Full prompt corpora were extracted for all five tools: personas, safety judges, subagent libraries (two-level index in [prompts/](prompts/README.md)). Two exceptions: Codex's Security Policy text is a runtime slot, not embedded; Droid has no such injected-policy slot at all.
- **Factory Droid ships its own source code.** 4,999 zstd frames in its Bun module graph decompress to 43.5 MB of original unminified modules (5,484 files), and a hidden judge persona scores the *user's* expertise from session transcripts with the org holding the consent switch.

## The three control planes at a glance

![control planes diagram](diagrams/control-planes-overview.svg)

<details>
<summary>Diagram source (mermaid)</summary>

```mermaid
flowchart LR
    subgraph AGY["agy · Antigravity"]
        LS["LanguageServerService<br/>348 methods · ConnectRPC<br/>localhost:5387"]
        SC["sidecar web server<br/>token-authed local HTTP"]
        BYO["AGY_LLM_GATEWAY_*<br/>bring-your-own-model"]
    end
    subgraph CLAUDE["claude · Claude Code"]
        GTW["claude gateway<br/>full HTTP server in-binary"]
        MCP["claude mcp serve<br/>the CLI as an MCP server"]
        CLD["cloud attach<br/>agent-proxy frames"]
    end
    subgraph CODEX["codex · Codex CLI"]
        AS["app-server<br/>102 methods · JSON-RPC-ish"]
        CM["code-mode-host<br/>Rust embedding V8"]
        AR["auto_review seat<br/>AI approves tool calls"]
    end
    YOU(["you / your scripts"]) --> LS & SC & BYO & GTW & MCP & CLD & AS & CM & AR
```

</details>

## What this unlocks (in plain English)

**1. Drive the Antigravity agent with plain web requests.** A local server exposes 348 control functions: start the agent, send messages, install plugins, open terminals. The program's own help text contains the exact curl recipe, so no SDK is needed. The full binary exposes 889 RPC methods across 30 services (finding #1).

**2. Codex prints its own instruction manual.** One built-in command emits all 102 client-to-server API methods as JSON Schema. Programmers stop guessing because the map comes from the tool itself.

**3. Claude Code's internals are now searchable text.** 41MB of internal JavaScript was pulled byte-exact from the binary. For permissions, settings, and cloud features, you can grep instead of guess.

**4. Public vs internal-only, read from the binary.** Mythos 5/5.1 has zero third-party provider IDs and no public alias; it is restricted to vetted partners. Fable 5/5.1 and GPT-6 Astra are public models whose catalog entries match the price lists.

**5. Antigravity's per-action safety screen, decoded.** A 3-stage pipeline runs before every tool call. It is configured from vendor servers, so the rules can change without an update. The override levers are mapped.

**6. Self-hostable servers inside the CLIs.** `claude gateway` is a complete HTTP server for routing AI traffic through your own infrastructure. Codex's code runner can point at a remote machine you own.

**7. An AI that approves the AI's tool calls.** Codex names an `auto_review` seat (legacy name: `guardian_subagent`), a prompted subagent that approves or denies tool calls in your place. The binary's own schema docs describe it as "a carefully prompted subagent to gather relevant context and apply a risk-based decision framework." The autonomy config ships today.

**8. Where your data goes, documented.** Antigravity has three telemetry pipelines and no program-level off switch. Codex analytics is off by default in the CLI (it only defaults on inside first-party hosts like the VS Code extension), while its OTel tracing is opt-in. Codex also phones home to a Sentry crash endpoint, a per-turn cost endpoint, and embeds `repo_hash` plus `line_fingerprints` in the analytics payload. Claude Code has a fully predictable permissions engine.

**9. The prompts the agents run on.** 135 prompts recovered verbatim: per-model system prompts and the full Guardian safety judge for Codex, the complete safety-judge texts and a hidden Teamwork swarm family for Antigravity, Claude Code's assembled prompt fragments (there is no single stored system prompt) plus its full security-review protocol, and Muse Code's main prompt in two editions.

## Receipts: cracked open, on the record

The internals were pulled out of the shipping binaries and then built on. This is a real terminal session against the installed `claude` binary:

![receipt: internal-only model family extracted from the binary](receipt-mythos-nulls.png)

Verbatim bytes from the binaries (offsets are in the finding docs):

```jsonc
// claude 2.1.287: the internal-only family. every third-party slot: null.
"claude-mythos-5-1": { "first_party": "claude-mythos-5-1",
  "bedrock": null, "vertex": null, "foundry": null,
  "anthropic_aws": null, "anthropic_google_cloud": null,
  "mantle": null, "gateway": null }
```

```jsonc
// codex: the binary's own schema describes who approves tool calls.
"ApprovalsReviewer": ["user", "auto_review", "guardian_subagent"]
// "auto_review uses a carefully prompted subagent to gather relevant context
//  and apply a risk-based decision framework... the legacy value
//  guardian_subagent is accepted for compatibility."
```

The carved sources are in [`carved/`](carved/): the Mythos registry entries as JSON, a slice of the minified shipped JS around the model-alias table (`best:"fable"`), and the opening of Antigravity's embedded 10.7KB safety pre-filter prompt, the secret rubric that screens every agent action.

[`pocs/`](pocs/) turns the findings into tools:

- a permission-rule **simulator** that predicts allow/deny before you run anything
- a settings **validator** against the recovered 183-key schema
- a surface **enumerator** for agy's control plane
- a model-catalog **differ** that flags new models, deprecations, and kill-switch flips on every future build

## Findings index, ranked by bigness

| # | Finding | Tool |
|---|---------|------|
| 1 | [The 889-method RPC service map: 30 services from codegen symbols](findings/antigravity/13-rpc-service-map.md) | agy |
| 2 | [The binary ships its own source: 50.5 MB of original modules recovered from the Bun module graph](findings/droid/03-source-recovery-method.md) | droid |
| 3 | [Self-documenting protocol: 102 client-to-server methods from the binary's own schema generator](findings/codex/01-app-server-protocol.md) | codex |
| 4 | [The full prompt corpus: every system prompt the binary ships](findings/codex/14-prompt-corpus.md) (new: the vendor's own instruction text, byte-exact, including a per-model `instructions_template` for gpt-6-astra) | codex |
| 5 | [One judge persona, three rubrics, and it scores the user; consent is an org-settings field](findings/droid/04-judges-and-localsignals.md) | droid |
| 6 | [Entire app carved out as 41MB of searchable JavaScript](findings/claude-code/01-bundle-surgery.md) | claude |
| 7 | [The prompt corpus: no single system prompt, just style preambles plus shared sections](findings/claude-code/17-prompt-corpus.md) (new: proves the system prompt is assembled from fragments, not stored; full security-review protocol recovered; the served prompt itself was captured live on 2026-10-20 and is compact, ~6K chars) | claude |
| 8 | [Model families: Fable 5/5.1 (public) and Mythos 5/5.1 (internal-only)](findings/claude-code/10-fable-mythos.md) | claude |
| 9 | [Local control plane: 348 methods, drivable with curl](findings/antigravity/01-local-control-plane.md) | agy |
| 10 | [The prompt corpus: personas are templates, and a Teamwork swarm ships inside](findings/antigravity/16-prompt-corpus.md) (new: the safety judge's full decision text plus an undocumented multi-agent swarm family) | agy |
| 11 | [GrowthBook is the experiment SDK: every `tengu_*` gate is a GrowthBook evaluation](findings/claude-code/13-growthbook-experiment-sdk.md) | claude |
| 12 | [The autonomy roadmap is a config surface: six experimental structs, fully field-recovered](findings/codex/11-roadmap-struct-fields.md) | codex |
| 13 | [Gated rerun: an independent verifier re-checked 226 claims against the frozen bytes](findings/codex/15-gated-rerun.md) (new: 23 prior claims overturned, analytics default flipped, Sentry DSN and cost endpoint found) | codex |
| 14 | [Gateway is a full self-hostable HTTP server, not just auth](findings/claude-code/06-gateway-server.md) | claude |
| 15 | [Per-step safety screen: 3 monitors, server-overridable](findings/antigravity/02-safety-screen.md) | agy |
| 16 | [Muse Code: the main prompt ships in two editions, no dedicated safety prompt](findings/muse/01-prompt-corpus.md) (new: first byte-level look at Meta's coding CLI) | muse |
| 17 | [Code-mode host: a Rust binary embedding V8 that runs raw JS cells](findings/codex/04-code-mode-host.md) | codex |
| 18 | [Permission engine decoded: deny > ask > allow, simulated exactly](findings/claude-code/03-permission-engine.md) | claude |
| 19 | [Update signing (RSA-4096 SPKI), Datadog sink, event logging](findings/claude-code/16-update-signing-datadog.md) | claude |
| 20 | [Sanctioned bring-your-own-model path (`AGY_LLM_GATEWAY_*`)](findings/antigravity/12-byo-model-path.md) | agy |
| 21 | [Cloud Run auto-updater: the real update host](findings/antigravity/15-cloud-run-updater.md) | agy |
| 22 | [Rate limits are readable AND redeemable (idempotency-keyed reset credits)](findings/codex/07-rate-limits.md) | codex |
| 23 | [The CLI is its own MCP server; first-party Gmail/GCal hosts](findings/claude-code/07-mcp-plane.md) | claude |
| 24 | [Unleash: the second flag system](findings/antigravity/14-unleash-flag-system.md) | agy |
| 25 | [Gateway full route table (18 paths)](findings/claude-code/15-gateway-route-table.md) | claude |
| 26 | [The code-mode sandbox is exactly 14 injected names (and no more)](findings/codex/12-cell-globals.md) | codex |
| 27 | [Hidden commands + unregistered `claude daemon`](findings/claude-code/14-hidden-commands.md) | claude |

Full prompt texts live in [`prompts/`](prompts/). The other finding docs live under [`findings/antigravity/`](findings/antigravity/), [`findings/claude-code/`](findings/claude-code/), [`findings/codex/`](findings/codex/), [`findings/muse/`](findings/muse/), and [`findings/droid/`](findings/droid/). The droid surface↔internals [crosswalk](findings/droid/crosswalk.md) maps every front-facing feature to its prompt section and mechanism, both ways.

## For developers

- **[Methodology](methodology/README.md):** techniques per target (Go pclntab parsing, Bun string-table carving, schema-generator subcommands, control experiments) and the instrument list.
- **[Eureka log](eureka-log.md):** chronological breakthroughs, with the exact command, offset, or pattern that cracked each surface.
- **[Internal intel](internal-intel/):** codenames, roadmap signals, and kill switches per tool. CONFIRMED vs INFERENCE is labeled and kills are documented.
- **[PoCs](pocs/):** runnable scripts, organized per tool, all re-run and passing.
- Every finding doc follows one template: **1.** WHAT WAS FOUND · **2.** HOW IT WAS FOUND · **3.** WHAT IT UNLOCKS · **4.** HOW A DEVELOPER BUILDS ON IT.

## Honesty box

Method, version pins, re-verification, and what was not verified.

**Method.** Strings, schema, and behavioral tier only: read-only Python extraction, targeted offset reads, live `--help` introspection, and each binary's own schema generators. Zero network calls, zero metered-model quota burned, binaries never modified.

**Version pins.**

- `agy` v1.3.1 (sha256 `085f43e0…455ef`)
- `claude` 2.1.287 (244,317,368 bytes, Bun)
- `codex` 0.155.1 + `codex-code-mode-host` 69MB.
- `muse` 1.4.7 (`muse-bin-1.4.7-R6101.1`, 363,518,168 bytes). Prompts pass only (2026-10-20).
- `droid` v0.245.0 (295,454,688 bytes, sha256 `61ad343a…fa18177cd`, matches Factory's published checksum). Note: the app-server schema baseline was first captured against 0.149.0 and refreshed to a fresh 0.155.1 emission on the reinforcement pass (finding 13 documents the delta); `gpt-6-astra` is a 0.155.1-era addition.
- Trials re-ran 2026-10-18/19.

**Re-verification.** 38 of 39 trials CONFIRMED live against the installed binaries. 1 is PARTIAL: `claude mcp list` hangs doing live health checks (it functions, but is unbounded without a timeout). All PoCs exit 0. Each finding gives per-byte evidence (offsets, quoted literals) so claims can be re-derived.

**Reinforcement (2026-10-19, independent tools: reverify, yara, LIEF, raw pread).**

- 40 load-bearing claims re-verified (8 claude + 17 codex + 15 agy).
- **15 figures corrected:**
  - claude: 199→183 keys, 1965→2133 manifest rows, "128"→549 gates
  - codex: 95/10/75/1→102/10/82/1, 97/101→101/101 fields
  - agy: 341→348/350 methods, BOQ 18→19, secrets 2→3, hooks 7→6, env 42→43
- **9 claims downgraded/refuted**, including `sprofile` (never existed), the `[UNSTABLE] FOR OPENAI INTERNAL USE ONLY` marker (zero hits in 0.155.1), and bulk prior `@`-offsets on agy.
- **6/6 kills confirmed.**
- ~281 new CONFIRMED internals.
- The systemic cause of the count errors, lossy packed-string-run tokenizing, is documented in [methodology](methodology/README.md) with the correct methods.

**Gated rerun + prompt pass (2026-10-20, `local-re-swarm`).**

- Codex claims re-gated against the re-pinned binary by a verifier that did not produce them: 188 priors (80 VERIFIED, 40 CORROBORATED, 45 UNVERIFIED, **23 DISAGREEMENT**) and 38 new claims (32 VERIFIED, 3 CORROBORATED, 3 DISAGREEMENT).
- **Corrections folded into the docs in place, dated 2026-10-20:** analytics default direction (finding 08), six-variant login blob and no-`id_token` tokens run (finding 06), ShellEnvironmentPolicy field list (finding 05), the `updater failed` literal (finding 13). Finding 15 is the full ledger.
- Prompt corpora extracted for all four tools (135 items). Muse is new to the repo: prompts only, no control-plane or telemetry pass yet.

**Droid deep pass (2026-10-20; first public map of the binary).**

- Four lanes (prompts/tools, telemetry, config, protocol) → two silo gap-audits → three
  brute-force waves → dynamic as-served capture (sandbox HOME + loopback stub, strace-verified,
  zero external hits) → closure wave → **source recovery** (Bun module-graph record store:
  4,999 zstd frames → 43.5 MB of original unminified source; 5,484 modules parse, recovered
  rubric builders generate sentences found byte-for-byte in the binary).
- All lane-doc claims re-gated against the recovered source: 64 claim clusters:
  42 VERIFIED, 5 CORROBORATED, 14 CORRECTED (18 dated errata filed), 3 UNVERIFIED.
  Wave-3 silo audit verdict: **READY-WITH-FIXES** (fixes filed).
- Honest residuals: software-factory worker prompts unrecovered (endpoints + gate wiring
  only); which copy of dual-stored prompts the served pipeline loads (static load path
  settled, no runtime trace).

**What was NOT verified.**

- Wire behavior of any protocol. No network was allowed, so per-method auth, framing, and concurrency come from schemas and strings, not observation.
- A live Antigravity language server. Nothing was listening; probing it needs a running server with a valid CSRF token.
- Whether `AGY_CLI_DISABLE_SAFETY_FILTERING` is honored.
- Servability of Mythos 5 via any real API (internal-only). Fable 5/5.1 and GPT-6 Astra are public models; the open question there is plan-gated CLI access, not existence.
- Per-key config defaults (~90/101 codex keys).
- Numeric telemetry tunables.
- Chunk-manifest u32 semantics (5 hypotheses dead, not re-chased).
- Per-method auth on all surfaces.

Gaps are labeled in-line, never smoothed over.

**Limits of the record.** Codex scratchpads for lanes A, C, D, E were reconstructed post-hoc from the lane deliverables (honest reconstruction headers inside). Where a finding was refuted (Agy's `--disable_telemetry` CLI-flag claim; the "Fable 5/5.1 unreleased" framing), the refutation is kept in the repo as a kill. A documented kill is a finding.
