# Internal intel - Factory Droid v0.245.0 (sha256 `61ad343a…fa18177cd`)

**CONFIRMED** = byte- or source-level evidence quoted in the deep-dive. **INFERENCE** = reasoned from evidence, gap named. **KILL** = chased and dead.

First public map of this binary (2026-10-20). Factory-AI's public GitHub publishes SDKs, the
GitHub Action, and tooling - the Droid CLI itself is closed source and none of the internals
below are public anywhere.

## Control surfaces (CONFIRMED)

- **One judge persona, three rubrics** scores sessions on triggers (session_end, compaction,
  todo_completion); the `expertise` rubric explicitly scores the **user**. Conversational text
  reaches the judge verbatim. Consent is an **org-settings** field
  (`advancedAnalyticsEnabled`, `ManagedSettingsSchema`).
- **Shadow risk classifier**: the independent op-risk classifier runs fire-and-forget, default
  off, contractually barred from enforcement. Live approvals use the model-authored label.
- **Alloy model router**: per-turn LLM classifier (default gpt-5.4-mini), 9 scored capability
  cards; org routing guidance is advisory only.
- **Droid Shield**: three layers (regex + two finetunes), token-logprob verdicts, fail-closed.
- **Permission flag reality**: `--skip-permissions-unsafe` drops only the confirmation layer;
  blocklists, policy preflight, and hooks still fire. A reserved destructive class asks for
  confirmation at any `--auto` level.
- **Act-as grants are backend-minted** (5-min TTL), never by the CLI; 167 `daemon.*` RPCs.
- **Telemetry off switch exists** (`telemetry.enabled: false`) but the org can force it on;
  **Sentry is always-on** (`sendDefaultPii: true`, argv incl. prompt in crash events);
  `machineId` ships unhashed.
- **ExitCourier**: exit-time delivery of queued telemetry + full cloud-sync message bodies,
  plaintext NDJSON spool, 30s deadline.
- **The binary ships its own source**: 5,484 modules / 50.5 MB of original unminified source
  recovered from the Bun module-graph record store - the strongest extraction in the repo.
- **Internal tooling shipped**: `droid dataset` / `droid experiments` (Factory-internal
  eval/experiment authoring), the `dogfood` internal-QA skill, a bespoke V8-isolate script
  engine (58.9 MB Rust ELF), and a `fff` LMDB file-finder ELF.
- **Checksummed binary-only updater** (SHA-256 hard gate, org can block). Registries:
  317 flags (142 default-TRUE), 109 cost blocks (multipliers, margin not computable), 251
  envs (incl. `FACTORY_E2E_*` fault injection), 61 first-party API paths.

## INFERENCE (gaps named)

- Whether the recovered source equals the exact shipped build commit (byte-matched rubrics
  and full parse census are strong, not a build hash).
- Which copy of dual-stored prompts the served pipeline loads (static load path settled via
  module-source imports; no runtime trace).
- Software-factory worker prompts unrecovered (endpoints + gate wiring only).

## KILL

- "Three separate judges" (one persona, three rubrics). "Pre-execution op-risk gate"
  (shadow only). "No telemetry off-switch" (exists). "Client-minted grants" (backend-minted).
  "machineId = hardware fingerprint" (daemon-protocol identity). "166 daemon methods" (167).
  "108 cost blocks" (109). "314 flags" (317). Source-maps in the binary (zero found).
