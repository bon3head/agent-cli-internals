# agent-cli-internals

The AI coding tools on your machine look like simple chat boxes: you type, they code. Underneath, each one is a full platform with a hidden control panel. This repo documents the panels.

Three tools were taken apart: Google's **Antigravity CLI** (`agy`), Anthropic's **Claude Code** (`claude`), and OpenAI's **Codex CLI** (`codex`). The team never ran the agents and never sent a single prompt to a model. Instead they read the programs' own install files — the text baked into them, the settings they ship with, and the self-describing specs some of them carry — and reconstructed what each tool can do, how it phones home, and where the steering wheels are hidden.

No models were queried. No accounts were touched. No files were changed. Everything here is byte-evidence: exact quotes from the installed software, with file offsets so anyone can re-check.

## What this unlocks (in plain English)

**1. You can drive the Antigravity agent from plain web requests, no official software kit needed.**
The program runs a local server on your own machine with 341 control functions — start the agent, send it messages, fork a conversation, install plugins, open terminals — and the program's own help text contains the exact recipe for calling them. Anyone writing a small script can now treat the whole AI as a remote-controlled instrument.

**2. Codex comes with its own instruction manual that writes itself.**
The program ships a command (`codex app-server generate-json-schema`) that prints out the complete map of all 95 things you can ask it to do, in a standard machine-readable format. Programmers no longer have to guess how to talk to it; the map is printed by the tool itself.

**3. Claude Code's entire brain was recovered as readable code.**
The program is packed as one big blob, but the team found the exact spot where the 41 megabytes of its internal JavaScript live and pulled it out byte-for-byte. Everything the app does — permissions, settings, cloud features — is now searchable text instead of a sealed black box.

**4. You can tell which models are public and which are internal-only.**
Claude Code's internal model catalog lists Fable 5/5.1 (public since June/September 2026) alongside Mythos 5/5.1 — the genuinely internal-only family, restricted to vetted partners, with every third-party provider ID null. Codex's files name GPT-6 Astra (public since September 3, 2026). The binary itself draws the line between public and internal.

**5. The "safety check" on every Antigravity action was fully decoded.**
Before every single thing Antigravity's agent does, a three-stage safety pipeline runs — and the configuration lives on the vendor's servers, meaning the rules can change without you ever updating the program. Researchers now know exactly what gets checked and where the override levers are.

**6. These tools are secretly servers you can self-host.**
Claude Code contains a complete web server (`claude gateway`) that can route AI traffic through your own infrastructure instead of the vendor's — built for companies that want control over where their data flows. Codex's sandboxed code-runner can also be pointed at a remote machine you own.

**7. Codex has an AI safety officer for its own actions, waiting in the wings.**
The code names a seat called `guardian_subagent`: an AI that reviews and approves the main AI's tool calls instead of asking you. Combined with token budgets that forcibly compact the conversation when spending limits are hit, this is the autonomy upgrade path — and the configuration already exists in today's release.

**8. The tools are honest about where your data goes — mostly.**
Antigravity reports what it sends home through three separate channels (including prompt text and file paths), and it has no program-level switch to turn usage reporting off. Codex cleanly separates its opt-in tracing from its always-on analytics, which does have an off switch. Claude Code's permissions engine is now fully predictable, so teams can write permission rules that behave exactly as intended instead of discovering surprises.

## Findings index, ranked by bigness

1. [Antigravity's local control plane: 341 methods, drivable with curl](findings/antigravity/01-local-control-plane.md)
2. [Codex's self-documenting protocol: 95 methods from the binary's own schema generator](findings/codex/01-app-server-protocol.md)
3. [Claude Code's entire app carved out as 41MB of searchable JavaScript](findings/claude-code/01-bundle-surgery.md)
4. [Model families: Fable 5/5.1 (public) and Mythos 5/5.1 (internal-only)](findings/claude-code/10-fable-mythos.md)
5. [Antigravity's per-step safety screen: 3 monitors, server-overridable](findings/antigravity/02-safety-screen.md)
6. [Claude Code's gateway is a full self-hostable HTTP server, not just auth](findings/claude-code/06-gateway-server.md)
7. [Codex's code-mode host: a Rust binary embedding V8 that runs raw JS cells](findings/codex/04-code-mode-host.md)
8. [Claude Code's permission engine decoded: deny > ask > allow, simulated exactly](findings/claude-code/03-permission-engine.md)
9. [Antigravity's sanctioned bring-your-own-model path (`AGY_LLM_GATEWAY_*`)](findings/antigravity/12-byo-model-path.md)
10. [Codex: rate limits are readable AND redeemable (idempotency-keyed reset credits)](findings/codex/07-rate-limits.md)
11. [Claude Code is its own MCP server (`claude mcp serve`); first-party Gmail/GCal hosts](findings/claude-code/07-mcp-plane.md)
12. [Antigravity telemetry: three pipelines, no program-level kill switch](findings/antigravity/05-telemetry.md)

*Note: the findings writers are building `findings/` docs in parallel per [PLAN.md](../PLAN.md). If any filename above differs from what's on disk, the on-disk name is authoritative.*

## For developers

- **[Methodology](methodology/README.md)** — the exact techniques used per target (Go pclntab parsing, Bun string-table carving, schema-generator subcommands, control experiments, adjudication) and the instrument list (Python `re` extraction, `dd` offsets, live `--help` introspection, schema generators).
- **[Eureka log](eureka-log.md)** — chronological breakthroughs with the exact command, offset, or pattern that cracked each surface.
- **[Internal intel](internal-intel/)** — per-tool codenames, roadmap signals, kill switches, and deprecations, every item labeled CONFIRMED or INFERENCE; kills documented.
- **[PoCs](pocs/)** — runnable proof-of-concept scripts, all re-run and passing, organized per tool.
- Each finding doc follows a fixed template: 1. WHAT WAS FOUND · 2. HOW IT WAS FOUND · 3. WHAT IT UNLOCKS (layman) · 4. HOW A DEVELOPER BUILDS ON IT.

## Honesty box

**Method:** strings/schema/behavioral tier only. Read-only Python extraction, targeted offset reads, live `--help` introspection, and each binary's own schema generators. Zero network calls, zero metered-model quota burned, binaries never modified.

**Version pins:** `agy` v1.3.1 (sha256 `085f43e0…455ef`) · `claude` 2.1.287 (244,317,368 bytes, Bun) · `codex` 0.155.1 + `codex-code-mode-host` 69MB (note: the app-server schema and feature-flag baselines were captured against 0.149.0; the trial found `gpt-6-astra` is a 0.155.1-era addition). Trials re-ran 2026-10-18/19.

**Re-verification:** 38 of 39 trials CONFIRMED live against the installed binaries; 1 PARTIAL (`claude mcp list` hangs doing live health checks — functions, but unbounded without a timeout). All PoCs exit 0. Per-byte evidence (offsets, quoted literals) is given in each finding so claims can be re-derived.

**What was NOT verified:** wire behavior of any protocol (no network allowed — per-method auth, framing, concurrency are from schemas/strings, not observation); a live Antigravity language server (nothing was listening — probing it needs a running server with a valid CSRF token); whether `AGY_CLI_DISABLE_SAFETY_FILTERING` is honored; servability of Mythos 5 via any real API (internal-only; Fable 5/5.1 and GPT-6 Astra are public models — the open question there is plan-gated CLI access, not existence); per-key config defaults (~90/101 keys each); numeric telemetry tunables. Gaps are labeled in-line, never smoothed over.

**Limits of the record:** Codex scratchpads for lanes A, C, D, E were reconstructed post-hoc from the lane deliverables (honest reconstruction headers inside). Where a finding was refuted (Agy's `--disable_telemetry` CLI-flag claim), the refutation is kept in the repo as a kill — a documented kill is a finding.
