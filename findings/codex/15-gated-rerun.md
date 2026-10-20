# 15. Gated rerun: an independent verifier re-checked 226 claims against the frozen bytes

**Run:** 2026-10-20, `local-re-swarm` v0.3.0. Target re-pinned before every gate: sha256 `0753dfe1…b761`, no drift.
**Method:** prior claims were transcribed by one context and gated by a different one. Evidence: `~/workspace/recon-swarm/runs/codex/findings/codex/` (REPORT.md, gated-priors.jsonl, claims.jsonl, eureka.jsonl hash chain verified).

## 1. WHAT WAS FOUND

**188 prior claims gated: 80 VERIFIED, 40 CORROBORATED, 45 UNVERIFIED, 23 DISAGREEMENT.**
**38 new lane claims gated: 32 VERIFIED, 3 CORROBORATED, 3 DISAGREEMENT, 0 UNVERIFIED.**

The 23 disagreements are the findings:

- **Analytics default was backwards.** Finding 08 called analytics ON by default. The embedded help text says analytics is disabled by default for the CLI/app-server, and defaults ON only when a first-party host (for example the VS Code extension) sets a hidden flag. Corrected in place in finding 08 (dated note, 2026-10-20).
- **The login blob holds six variant names, not five:** `apiKey, chatgpt, chatgptDeviceCode, chatgptAuthTokens, amazonBedrock, amazonBedrockAccessKeys`. Finding 06 corrected in place.
- **The tokens blob has no `id_token`:** `access_token, refresh_token, account_id, chatgpt_user_id, user_id, chatgpt_account_id, chatgpt_account_is_fedram`.
- **`max_depth` is not a ShellEnvironmentPolicy field.** The FIELDS walk gives 7 fields: inherit, ignore_default_excludes, exclude, set, include_only, filters, experimental_use_profile. Finding 05 corrected in place.
- **Systematic count undercounts (off by 1–7)** across error-string censuses from the first pass, same lossy packed-run cause as the 2026-10-19 corrections. Example: `failed to parse plugin ` is 21, not 14.
- **`updater failed` has zero hits as a prefix.** The literals are `failed to resolve current updater executable` and kin, packed adjacent. Finding 13's quoted form was a packed-run misread, corrected in place.
- **Three named strings have zero hits in 0.155.1:** `IpSocketSessionCellExecutionLimits`, `ClientHelloWire`, `struct WireToolDefinition`.
- **New channels (verified, addendum in finding 08):** an embedded Sentry crash DSN, a per-turn cost endpoint `https://api.chatgpt.com/v1/analytics/codex/turn-costs`, an analytics events path, and `codex_turn_event` fields carrying `line_fingerprints` and `repo_hash`.
- **Update path:** update checks read GitHub releases, the Homebrew cask JSON, and `chatgpt.com/codex/install.sh`; state persists as `VersionInfo{latest_version, last_checked_at, dismissed_version}`. The standalone updater is passed to a shell: `/bin/sh` + `-s` with `CODEX_RELEASE` / `CODEX_UPDATE_FROM_RELEASE` in the adjacent literals (offset 219190669).
- **Also new:** 104 distinct `CODEX_*` env names (18 of them `CODEX_SNAPSHOT*` exec-snapshot names); embedded SQLite DDL for ~20 state tables (`threads`, `remote_control_enrollments`, `thread_goal_continuation_deferrals`); exec-server rendezvous over websocket with a Noise protocol; remote-control pairing rejects a mismatched enrollment `server_id`.

Three new claims were also disputed and stay labeled: single-method namespaces are 10, not 11; the metrics census headline (199) does not reproduce (198 strict, 321 boundary-split); one claim's field gloss contradicted its own verified field list.

## 2. HOW IT WAS FOUND

Two light lanes (static-inventory, telemetry-tracer) re-derived evidence against the frozen bytes, then a fresh verifier context gated every claim: byte claims through `reverify`, counts through an independent scanner (never grep line counts). Static only: no live capture; heavy tools off by RAM constraint. The one behavior-checkable claim (`codex login start`, exit 2) was decided by running the pinned binary.

## 3. WHAT IT UNLOCKS

The first pass was good but not exact, and the errors were systematic, not random: packed string runs undercount, and prefixes get invented at run boundaries. The rerun converts "trust the doc" into "trust the gate": every surviving claim has an independent verdict attached, and every overturned claim keeps its correction in writing.

## 4. HOW A DEVELOPER BUILDS ON IT

- Gate before you publish: transcribe claims, then verify in a fresh context with a different instrument than the producer's.
- Never count packed runs. Use the FIELDS statics, the schema generator, or raw substring census with the method named.
- Treat any quoted literal longer than the run that contains it as suspect until a byte-exact check passes.
