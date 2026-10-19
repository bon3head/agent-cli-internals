# 14. Unleash: the second flag system

**Trial status:** CONFIRMED. The binary vendors `third_party/golang/github_com/Unleash/unleash_client_go/v4` with a jetski wrapper and a hard-coded Unleash server endpoint. Prior coverage (A5) documented only Mendel. This doc covers what the second system is and what two coexisting flag systems means.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 1. WHAT WAS FOUND

**agy ships two independent feature-flag/experiment systems: Mendel (already documented) and Unleash (new).** The Unleash evidence:

- **Vendored client:** `third_party/golang/github_com/Unleash/unleash_client_go/v4`: Unleash's official Go client, linked into the binary.
- **jetski wrapper package:** `google3/third_party/jetski/unleash/`, character region @12627612–12631594, exposing a full read-by-name API surface: `InitializeUnleash`, `DisableUnleash`, `NewUnleashWrapper`, `IsEnabledByName` / `UnsafeIsEnabledByName`, `GetVariantByName` / `UnsafeGetVariantByName`, `ReadVariantIntPayloadByName` / `ReadVariantFloatPayloadByName`, `ToExperimentJson` / `ToExperimentVariantJson`, `UpdateDevExperimentOverride`, `UpdateBaseExperimentConfig`, plus a listener `OnWarning`. The `ByName` read pattern plus typed variant-payload readers means experiments are looked up by string key and can carry int/float payloads (thresholds, budgets, variants).
- **Server endpoint:** `https://antigravity-unleash.goog/api/` @91741293: the Unleash feature-flag server base the client talks to (a Google-internal `.goog` domain, not a public SaaS Unleash instance).
- **Wiring into the agent surface:** the LanguageServerService exposes `GetUnleashData` @28033759 and `ShouldEnableUnleash` @28014240 as RPCs: the local server computes or relays Unleash state to the CLI. Mendel side: `GetMendelFlags` @28033889, `SetMendelFlagOverrides` @28034019, plus `UpdateDevExperiments` / `UpdateEnterpriseExperimentsFromUrl`.

**What the two systems appear to split** (INFERENCE: the source doc marks attribution explicitly, and this doc preserves the label): Unleash toggles/variants are the likely consumer of the embedded 40-key kebab-case flag-defaults JSON (`base`/subclients/model_profiles @188422497–188427500: `checkpoint-variant="claude-1m_840k"`, `enable-sidecars=true`, `tool-output-max-bytes=10240`, …), i.e. client-evaluated on/off switches and variant payloads. Mendel handles polled server-driven flag state (`MendelStateCache.pollLoop`, `GetEffectiveFlags`, `GetEffectiveExperimentIDs`, `NewPolledMendelAdapter` @0x6cb4a60) i.e. experiment assignments pushed/polled from the server. The name->system mapping for any given flag key is **unrecoverable at strings tier**: both `MendelAdapter).GetString/IsEnabled` and `unleash.(*UnleashWrapper).IsEnabledByName/GetVariantByName` read flags by name, and the binary contains no key-to-system table.

**What this corrects:** nothing prior said about flags is wrong: Mendel evidence (poll adapter, `GetMendelFlags` RPC, `MendelExperimentIds` on trajectory metadata, `BORG_EXPERIMENTS`/`BORG_DISABLE_EXPERIMENTS`) all stands. The correction is additive: any "the flag system" claim from prior docs is now ambiguous between two systems. Dated note (2026-10-19): prior docs' Mendel-only framing superseded; flag behavior observed in the wild could be driven by either Mendel assignments or Unleash toggles, and `GetMendelFlags` on the LS exposes only one of the two.

---

## 2. HOW IT WAS FOUND

Lane DEPTH-INTEL, strings tier, against the sha256-verified binary (`sha256sum` first command).

- `strings -a -t d /home/hatch/.local/bin/agy > agy.strings.txt` (66MB, 1,924,440 lines; first column = rodata file byte offset, cited as `@N`)
- Unleash vendored path + wrapper API names recovered from package-path greps: `third_party/golang/github_com/Unleash/unleash_client_go/v4` and `google3/third_party/jetski/unleash/` (@12627612–12631594) with the full API list quoted above (`InitializeUnleash` … `OnWarning`)
- Endpoint: `grep -F 'https://antigravity-unleash.goog/api/' agy.strings.txt` -> @91741293 (single hit; server base for the Unleash client)
- LS RPC methods from the DEPTH-GRPC Unimplemented-symbol inventory: `GetUnleashData` @28033759, `ShouldEnableUnleash` @28014240, `GetMendelFlags` @28033889, `SetMendelFlagOverrides` @28034019 (all in `~/workspace/re-suite/findings/agy/grpc-methods-LanguageServerService.tsv`)
- Mendel infra from pclntab symbol recovery (DEPTH-GORESYM): `google3/third_party/jetski/experiments/experiments`; `NewMendelAdapter` @0x6cb4820, `NewPolledMendelAdapter` @0x6cb4a60, `(*MendelStateCache).pollLoop/GetEffectiveFlags/GetEffectiveExperimentIDs` @0x6cb59a0–0x6cb6220
- Embedded 40-key flag-defaults JSON carved at @188422497–188427500 (shape `{"base": {...}, "subclients": {"CLI":…,"IDE":…,"SDK":…}, "model_profiles": {...}}`)

---

## 3. WHAT IT UNLOCKS

Think of it this way: the program has two separate remote-control channels for flipping features. One (Mendel) is the server's experiment desk: it polls in the background and assigns you to test groups. The other (Unleash) is a standard off-the-shelf feature-toggle service hosted inside Google, which the program checks by name when it needs to ask "is this thing on, and what variant am I in?" Because both exist, a behavior that changes day to day might be a Mendel experiment OR an Unleash toggle, and the program's own "show me the flags" RPC only exposes one of them. Anyone trying to understand or reproduce a behavior change now knows to check both, and knows the local server has dedicated RPCs (`GetUnleashData`, `ShouldEnableUnleash`) that can reveal the Unleash side.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Live flag inspection:** `GetMendelFlags` (Mendel side) and `GetUnleashData` (Unleash side) on the LS at localhost:5387; call both; prior docs' Mendel-only guidance misses the second system.
- **Toggle watching:** the Unleash server base is `https://antigravity-unleash.goog/api/`: flag *names* (not values) can be harvested from client-side `IsEnabledByName`/`GetVariantByName` call sites; values are server-side and authed.
- **Experiment reproduction:** when reproducing a behavior, pin both systems: `UpdateDevExperimentOverride` (Unleash, client-side override exists) and `SetMendelFlagOverrides` (Mendel, requires developer mode; `Applying %d developer Mendel flag overrides`, `Mendel flag overrides require developer mode`).
- **Flag-key attribution:** any given kebab-case key (e.g. from the @188422497 embedded defaults block) must be tested against BOTH `(*MendelAdapter).IsEnabled` and `unleash.(*UnleashWrapper).IsEnabledByName`: there is no in-binary key-to-system table, so do not assert which system owns a key without runtime evidence.
- **`DisableUnleash` exists as a wrapper API**: investigate its wiring if you need a client-side kill path for the Unleash layer.
