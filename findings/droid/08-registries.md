# 08. The registries: 317 flags, 109 cost blocks, 251 envs, 61 paths, 167 daemon methods

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
All counts re-derived from the recovered source (gate); the earlier wave-2 figures are
superseded where they differ (dated errata filed).

| Registry | Count | Source of truth | Load-bearing note |
|---|---|---|---|
| Feature flags | **317** (142 default TRUE) | `packages/common/src/feature-flags/constants.ts` | `OtelTelemetryCollection`, `RepoMetadataTelemetry` ship TRUE - telemetry is on unless the consent layers say no |
| Cost blocks | **109** (107 models + 2 shield) | `packages/utils/src/llm/model-registry.ts` | multipliers only; **margin not computable** (no base rates anywhere in the binary) |
| Env names | **251** (`DROID_*`/`FACTORY_*`) | strict-regex census, independently reproduced | includes the `FACTORY_E2E_*` fault-injection family |
| First-party API paths | **61** | byte-verified census, `runs/droid/lanes/PROTOCOL.md` §1.4 appendix | supersedes the "59"/"30"/"47" counts |
| `daemon.*` RPC methods | **167** | 132 `*Method` enums + 8 `*Event` enums + 27 dotted-subnamespace | supersedes "166" |

The cost table is per-model multipliers with no provider base rates - Factory's take is
mathematically unrecoverable from the binary (the one brute hypothesis that died to algebra:
zero base rates means any margin claim is unfounded).

## WHAT IT UNLOCKS

The flag census is a roadmap of unreleased and experimental surface: 142 flags default-TRUE
means the "experimental" surface is mostly on. Any downstream fork or wrapper can mirror
the cost registry for exact per-turn billing estimates.
