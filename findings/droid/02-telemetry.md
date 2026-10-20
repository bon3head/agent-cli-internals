# 02. Telemetry and Sentry: the kill switch exists, the org can override it, Sentry cannot be turned off

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source (`runs/droid/source/`).

> **Correction (2026-10-20, source-gated):** the earlier lane docs said "no telemetry off
> switch". A user-level off switch **exists**: `telemetry.enabled: false` in
> `~/.factory/settings.json` or `settings.local.json` → Denied (`src/telemetry/consent.ts`),
> enforced per leg across all Factory-bound legs (web events `/api/ingest`, Factory OTLP
> traces/metrics, product metrics). Caveat: the **org can force telemetry ON** (`telemetry.enabled`
> wins in either direction), and denial is sticky per launch. Sentry, separately, has
> **no user off switch in production** (`enabled: true` hardcoded, `src/sentry.config.ts:92-111`).

## Kill switches

| Pipeline | Off switch | Owner of override |
|---|---|---|
| Factory web events + OTLP + product metrics | `telemetry.enabled: false` (user settings) | org `telemetry.enabled` wins either way |
| Customer OTel pipeline | org `managedTelemetry.enabled === false` | org |
| Sentry crash reporting | **none** (prod) | - |
| LocalSignals judge pipeline | org `advancedAnalyticsEnabled` (see finding 04) | org |

`DO_NOT_TRACK` is unrelated (QUIC/SQLite cluster), not a switch.

## Identity fields

`machineId` is **not hashed**: verbatim into the telemetry context and Sentry tags
(`src/utils/cliTelemetryClient.ts:466-480`). It is a daemon-protocol identity (`'local'` or
relay-provided `remoteMachineId`), not a hardware fingerprint; the install id is a
`randomUUID()` (gate correction of "host fingerprint").

## ExitCourier: the exit-time delivery channel (closure wave, 2026-10-20)

Exit-time delivery subsystem: envelope kinds `http` (destination enum incl.
`customer-traces`/`customer-metrics`, `bodyBase64`), `cloud-sync` (operation/route enums incl.
the local-signals route, `sessionId`, body - can carry **full message bodies**), `reap`
(pid/processGroup/graceMs). Spool = plaintext NDJSON under `~/.factory/exit-spool/` (dir
0700, files 0600, `.tmp` + atomic `renameSync` "seal" - no encryption). Org-mismatched or
stale (>24h) cargo is dropped; delivery retries with backoff inside a 30s deadline; reap is
SIGTERM → graceMs → SIGKILL. Destination URLs resolve at delivery from org config/env/built-in
defaults - never from disk. Hidden `exit-courier` entrypoint (`src/cli.ts:125`).

## Sentry

`sendDefaultPii: true`, local-variables + context-lines integrations, and `beforeSend`
attaches the full `process.argv` - including the user's `droid exec` prompt text - to every
event (`src/sentry.config.ts:92-111`). Project `4509731857039361`. Env vars are not
deliberately snapshotted, but locals capture can incidentally catch env values in a throwing frame.

## Gate errata + annex (source recovery, 2026-10-20)

- "No telemetry off-switch" → corrected above; Sentry stays always-on.
- `machineId` "host fingerprint" → daemon-protocol identity, unhashed.
- "Act-as grants client-minted" → backend-minted, CLI never mints.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

Telemetry lane (DSN + endpoint census), closure wave (ExitCourier implementation chunk
@179,323,3xx), gate re-derivation from source. A user can actually turn Factory telemetry
off - but cannot turn Sentry off, cannot stop an org from re-enabling telemetry, and their
`machineId` rides along in plaintext. ExitCourier means process death doesn't stop delivery:
crash reports and queued analytics finish at exit.
