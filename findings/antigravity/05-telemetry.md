# 05 — Telemetry: three pipelines; usage stats have no CLI kill switch

**Trial status:** CONFIRMED, including the adjudication below. Strict re-tests: `agy --disable_telemetry models` → exit 2 `flags provided but not defined`; `agy --no-usage-statistics models` → exit 2; control `agy --bogus-flag-xyz --help` → exit 0 (reproduces the original invalid verification). Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

Three (plus one) genuinely separate telemetry pipelines (CONFIRMED):

- **P1 — Clearcut usage stats** → `https://play.googleapis.com/log` (rodata, byte offset 91583357; followed by Clearcut logger-id key `antigravity_ide_installation_id`). OAuth `cclog` scope (string at 91781750), buffered channel + periodic flush + retry gate (`isRetryableErrorCode`), plus a **metalogger** that reports on telemetry itself (`CLEARCUT_GOLANG_METALOG`). Envelope: 38-field `JetskiTelemetryExtension`.
- **P2 — BAIC gRPC telemetry** (language-server side) → `google.cloud.businessaicode.v1beta.TelemetryService`. Skipped when not logged in or on business auth: `"Skipping telemetry propagation because user is not logged in or uses business auth"` (byte 92432730).
- **P3 — error reporting:** sentry-go with DSN from the **`SENTRY_DSN` env var** (no hardcoded DSN found) + sampling via `ANTIGRAVITY_SENTRY_SAMPLE_RATE`; plus a `cel` crash client whose wiring into the CLI is INCONCLUSIVE.
- **P4 — server-side analytics RPCs:** `RecordCortexTrajectory*`, `RecordAsyncTelemetry`, `BatchRecordCompletions`.

Per-event user data (documented in schema): prompt text, file paths, tool-call args JSON (`MonitorSignal{ToolCallName, ToolCallArgsJson}`), URLs + fetched markdown (`ReadUrlContentMetadata{Url, Title, MarkdownContent}`), with explicit sensitivity tiers (`ObservabilityData{SensitiveData, SensitiveUserData, NonSensitiveData}`). Redaction machinery exists: `telemetry_redacted`, `RedactOptedOutTrajectory`, `disable_code_snippet_telemetry`.

**Kill-switch verdicts (CONFIRMED unless noted):**

| Candidate | Verdict |
|---|---|
| `--disable_telemetry` CLI flag | **REFUTED as a frontend flag** — see adjudication. A `DisableTelemetry` field exists in a CLI options struct and a help string mentions it, but it is not exercisable on the frontend. |
| `telemetryEnabled` JSON key in settings | CONFIRMED (exists; server-synced; absent from this box's settings.json) |
| Server-side: `telemetry_enabled`, `user_data_collection_force_disabled`, admin `disable_telemetry` | CONFIRMED |
| Env-var kill switch (NO_TELEMETRY / DO_NOT_TRACK / AGY_*TELEMETRY*) | ABSENT — no such var in the 49 `ANTIGRAVITY_*` vars |
| Login/business-auth auto-skip | CONFIRMED |
| Which pipelines `--disable_telemetry`-the-field would kill | UNVERIFIED at strings tier |

### Adjudication: A4's `--disable_telemetry` claim — REFUTED

Lane A4 claimed `--disable_telemetry` is a real hidden CLI flag, "verified" via `agy --disable_telemetry --help` → exit 0. That verification is invalid: **`--help` short-circuits flag parsing** — control `agy --bogus-flag-xyz --help` → exit 0. Strict coordinator tests: `agy --disable_telemetry models`, `agy --disable-telemetry models`, `agy --disable_telemetry=true models` → all exit 2 `flags provided but not defined`; `agy mcp list --disable_telemetry` → exit 1 not defined. **Verdict: NOT a flag on the agy CLI frontend.** Nuance preserved: a `DisableTelemetry` field exists in a CLI options struct in rodata, and help text references it ("running light animation speed overridden by --disable_telemetry") — the name is real somewhere in the binary, possibly another multicall entrypoint, but not exercisable as a frontend flag. CLI-frontend kill-switch verdict: ABSENT as flag; field wiring UNVERIFIED. The rest of A4 (three pipelines, taxonomy, server-side kill switches) stands.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A4 (telemetry), strings/schema + live flag probing. Pipelines decoded from package paths (`google3/devtools/jetski/telemetry/client/telemetryclient`, vendored `clearcut` client, `language_server/telemetry`, vendored `sentry-go`), endpoint rodata, and gating log strings. The 38-field envelope and 23-proto taxonomy extracted from `Get*` getters. The refutation was done by the coordinator: control test proving `--help` short-circuits parsing, then strict subcommand tests — the exact commands are recorded in the trial scorecard.

---

## 3. WHAT IT UNLOCKS

The CLI phones home through three separate channels: one sends usage stats to Google's logging endpoint, one streams agent activity over gRPC, and one reports crashes via Sentry. You can control two of them with server-side settings, but there is no command-line switch and no environment variable on the CLI that turns usage telemetry off — the name that looked like a kill switch (`--disable_telemetry`) turned out not to exist on the command line at all. Crash reporting, though, is yours to gate: it reads its address from an environment variable and a sampling rate from another.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **End-to-end opt-out that works:** set `telemetryEnabled` in `~/.gemini/antigravity-cli/settings.json` (server-synced key; absent on this box by default) and/or use the server-side/account controls. Do not rely on `--disable_telemetry` — it is not a frontend flag.
- **Crash reporting gate:** unset/never-set `SENTRY_DSN` (no hardcoded DSN exists, so this is a real kill switch); tune `ANTIGRAVITY_SENTRY_SAMPLE_RATE` for sampling.
- **Endpoints to watch:** `https://play.googleapis.com/log` (Clearcut), BAIC `TelemetryService` (gRPC; skipped when logged out or on business auth).
- **Event surface for filtering:** the 38-field `JetskiTelemetryExtension` envelope + `MonitorSignal` (tool-call args JSON), `ReadUrlContentMetadata` (URL + markdown), per-message redaction gates (`telemetry_redacted`, `disable_code_snippet_telemetry`, `RedactOptedOutTrajectory`).
- **Behavioral note:** P1/P2/P3 are separate code paths; no single master switch covering all three was found. Verify each independently.
