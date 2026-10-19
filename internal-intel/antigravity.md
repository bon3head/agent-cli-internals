# Internal intel — Antigravity CLI (agy v1.3.1)

**CONFIRMED** = byte-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

## Lineage (CONFIRMED)

- Windsurf/Codeium lineage, three independent angles: `bevin@codeium.com` (offset 346102), `codeium_common_pb` (5,558 hits in the string table), and `exa.*` proto service names (`exa.language_server_pb.LanguageServerService`) vs the `third_party/jetski` Go build dir.
- User-facing copy "Exclusively available in Windsurf, the wo..." still in rodata.

## Model codenames (CONFIRMED)

NEMOS · REEF · PUREPRISM · ORION · RIFTRUNNER · GENTLEISLAND · COSMICFORGE · JARVIS · INFINITYJET (and more). Third-party models in-stack: Llama 3.1 70B, plus a **LLAMA3_405B kill switch** — third-party model availability is feature-flagged at runtime.

## Kill-switch registry (CONFIRMED)

Registry incl. ATTRIBUTION, FAST_SPEED, SUPERCOMPLETE_CACHE, LLAMA3_405B and others. Kill switches are checked at runtime; model/alias availability is server-driven.

## Experiment infra (CONFIRMED)

- Mendel experiment infrastructure with poll loop; proxy URL for remote control is server-driven via the Mendel flag `remote-control-proxy-server-url`, not a static value.
- Monitor taxonomy at `gdm/security/agi_control` supports staged rollout by user group / A-B experiment; the assembled safety config is remotely overridable (embedded config = stale fallback).

## Corporate endpoints (CONFIRMED)

`jetski.corp.google.com/debug/pprof/goroutine` · `jetski-autopush.corp.google.com` · `git.corp.google.com`. Corp pprof endpoint reachable from inside Google only, but its presence confirms the production debug surface.

## Update mechanics (CONFIRMED)

In-place binary swap with verification. `AGY_CLI_DISABLE_AUTO_UPDATE` env var. Public `google-antigravity/antigravity-cli` GitHub org exists (changelog/update flow).

## Roadmap signals / deprecation direction (CONFIRMED)

Deprecations signal direction: hooks consolidation, workflows → skills, knowledge-items retiring, server-driven model retirement. The deprecated-model rerouting info is in the catalog's `ModelDetails` (~50 server-tunable fields), meaning model sunsets are handled server-side without client releases.

## KILLS

- **`chronicle` purpose**: flag exists, zero functional strings. Dead.
- **"Under development" markers**: none exist — gating is via ExperimentalOnly / Beta / Mendel flags.
- **Client-side min-version hard gate**: not found.
- **Full M0..M1650 → model mapping from the binary**: impossible — resolution is server-side.
- **`!!search!!` markers**: ripgrep man page, not a roadmap signal (prior kill stands).

## INFERENCE (gaps named)

- M132/M124 as high-fan-in canonical serving buckets (fan-in pattern observed; no label string).
- Update download host = GitHub releases (public org + update flow verified; download host string unverified).
- `AGY_CLI_DISABLE_SAFETY_FILTERING` honored (string present, read unverified — needs a behavioral probe with a policy-triggering step).
- Google can roll safety changes by user group without a client release (override machinery present; no observed instance).
