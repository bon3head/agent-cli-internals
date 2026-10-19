# 11 — Internal intel overview: lineage, codenames, kill switches, update mechanics

**Trial status:** CONFIRMED. Lineage spot-checks: `bevin@codeium.com` 1 hit, `codeium_common_pb` 5558 hits, `jetski.corp.google.com` 2 hits. `chronicle` KILLED (no subcommand in `agy --help`; zero functional strings). Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

**Windsurf/Codeium lineage (CONFIRMED, three independent signals):** `bevin@codeium.com` (strings :346102), `codeium_common_pb` (5558 string-table hits; `EventType`, `CascadeNUXEvent` in `jetski/codeium_common_pb`), and the proto namespace `exa.*` vs the Go build dir `third_party/jetski` — consistent with Google's 2025 Windsurf talent acquisition. 88% of the 164,366 functions sit under `google3/` — a google3-built binary, not GitHub-built. Top dirs: `google3/third_party/golang` (deps), `google3/third_party/jetski` (~83k refs — the product), `google3/learning/genai` (incl. `beyond/` = model serving/quota), `google3/google/internal` (`cloud/code`, `alkali`, `businessaicode`), `google3/gdm/security/agi_control` (agent safety monitors).

**Codenames (CONFIRMED, exact strings):** runtime — `jetski` (whole codebase), `exa` (proto namespace), `cascade` (agent), `cortex` (agent runtime), `sobi` (agent harness), `jetbox` (state/summaries), `beyond` (model serving/quota). Models — NEMOS, REEF, PUREPRISM, ORION, COSMICFORGE, JARVIS (incl. `JARVIS_V4S`, `JARVIS_PROXY`), RIFTRUNNER, GENTLEISLAND, INFINITYJET, INFINITYBLOOM, plus Claude (`4_OPUS_THINKING`, `4_5_SONNET`, `4_5_HAIKU_THINKING`), GPT (`GPT_OSS_120B_MEDIUM`), Llama (`3_1_70B_INSTRUCT_LONG_CONTEXT_VARIANTS`). **Third-party models in-stack:** `LLAMA3_405B_KILL_SWITCH` sits in the kill-switch registry alongside `ATTRIBUTION_KILL_SWITCH`, `FAST_SPEED_KILL_SWITCH`, `SUPERCOMPLETE_CACHE_ON_PARENT_ID_KILL_SWITCH`, `NON_TEAMS_KILL_SWITCH`.

**Rollout machinery (CONFIRMED):** Mendel experiment infra (`NewPolledMendelAdapter` with pollLoop; `MendelExperimentIds` on trajectory/step metadata), RPCs `UpdateDevExperiments` / `UpdateEnterpriseExperimentsFromUrl`. Gating is via `ExperimentalOnly`/`Beta`/`Preview`/`DeprecatedModelIds`/Mendel — zero "under development" markers exist (killed).

**Update mechanics (CONFIRMED + one INFERENCE):** in-place binary swap with verification — strings `Checking for updates... (current version %s)`, `Verification successful.`, `Swap Phase 1 Failure: %v` / `Swap Phase 2 Failure: %v`, `malformed ELF binary`. Public surface leak: `https://raw.githubusercontent.com/google-antigravity/antigravity-cli/refs/heads/main/CHANGELOG.md` — a PUBLIC `google-antigravity` GitHub org hosting `antigravity-cli`, used by the changelog/update flow. **INFERENCE:** update artifacts likely download via GitHub releases from that org — unverified (download host not in cleartext). Insiders channel: `/google/data/ro/teams/jetski-fix/glinux-insiders/latest/linux-x64/...`. Kill switch: `AGY_CLI_DISABLE_AUTO_UPDATE`. No client-side min-version hard gate (killed; server-side gating only via NUX filters / model rerouting).

**Corp endpoints (CONFIRMED):** `https://jetski.corp.google.com/debug/pprof/goroutine`, `https://jetski-autopush.corp.google.com`, `git.corp.google.com`, `https://gaiastaging.corp.google.com`.

**Deprecation direction (CONFIRMED):** hooks consolidation (pre-invocation hooks + post-invocation `conversation_log` deprecated), workflows deprecated in favor of skills, knowledge-items retiring (`GetKnowledgeItems is deprecated`), server-driven model retirement (`DeprecatedModelReroutingInfo`). `chronicle` = KILLED (flag exists, zero functional strings, no subcommand).

**`chronicle` kill:** verified live — `agy --help` shows `Available subcommands: agent agents changelog help install mcp mic-serve models plugin plugins remote-control update` (no `chronicle`, no `features`).

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A5 (internal intel), strings tier. Lineage triangulated from email + proto package + namespace/build-dir mismatch. Kill-switch registry carved at strings :496057-496294. Corp endpoints from exact-substring greps. Update mechanics from updater package strings (`third_party/jetski/cli/updater/`). Trial spot-checks: `grep -cF` for the three lineage signals; `agy --help` subcommand census.

---

## 3. WHAT IT UNLOCKS

The program's fingerprints tell its biography: it grew out of Windsurf/Codeium code, is built inside Google's monorepo, and its servers know models by secret codenames — including rival companies' models behind remote kill switches. Updates swap the binary in place with a verification step, and the public changelog lives in a GitHub org Google hasn't hidden. The direction of travel is readable too: workflows are being retired for skills, and model retirements are pushed from the server, not shipped in releases.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Track releases:** `https://raw.githubusercontent.com/google-antigravity/antigravity-cli/refs/heads/main/CHANGELOG.md` — public org; watch it for update signals independent of the auto-updater.
- **Disable auto-update:** `AGY_CLI_DISABLE_AUTO_UPDATE` (env).
- **Kill-switch watchlist:** `ATTRIBUTION_KILL_SWITCH`, `LLAMA3_405B_KILL_SWITCH`, `FAST_SPEED_KILL_SWITCH`, `SUPERCOMPLETE_CACHE_ON_PARENT_ID_KILL_SWITCH`, `ESTIMATE_TOKENIZER_KILL_SWITCH`, `NON_TEAMS_KILL_SWITCH` — server-pushed; check their state via `GetMendelFlags` / `GetServerConfiguration` on the LS.
- **Model codename decoding:** when logs reference NEMOS/REEF/JARVIS/etc., these are the `MODEL_*` enum family — the public names are only pinned by the server catalog.
- **Forward-compat:** build against skills, not workflows (deprecated); read `DeprecatedModelReroutingInfo` rather than hardcoding model IDs; expect hook-system consolidation to continue.
- **Mendel experiments:** `GetMendelFlags` on the LS exposes the live experiment/flag state driving behavior and the remote-control proxy URL.
