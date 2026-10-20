# 01. Config and permissions: 251 envs, the real flag semantics, 167 daemon RPCs, hidden internal tooling

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`
(matches Factory's published checksum). All claims below were gate-checked against the
binary's own recovered original source (`runs/droid/source/`), 5,484 modules; source paths
are that tree. Full rigor artifact: `findings/droid/crosswalk.md` ties every surface item
to its prompt section and module.

## 1. Env surface (251 names)

251 distinct `DROID_*` / `FACTORY_*` names (strict regex census, independently reproduced
exactly). Includes a shipped **fault-injection family** (`FACTORY_E2E_*`): crash-on-prompt,
disk faults, slow paths, clock skew - test hooks in the public binary.

## 3. Permission model

**`--skip-permissions-unsafe` does NOT disable permissions.** Source-verified
(`src/entrypoints/exec/`): the flag disables only the **confirmation** layer
(`shouldConfirmExecution.ts:619-622`). Still firing under it: blocklist deny
(`src/agent/tools.ts:1344`), `runSingleToolPolicyPreflight` (`:1786-1814`), PreToolUse hooks
(`:1501-1540`, precedence block > ask > allow > no-match), and the Execute executor's
blocklist re-check (`execute-cli.ts:450-472`). The hard `block` class "can never run and can
never be approved" (`SessionConfigService.ts:237-244`). Mutual exclusion with `--auto`
confirmed (`assertValidOptions.ts:243`).

**A reserved destructive class sits above `--auto high`.** Some commands ask for explicit
confirmation no matter how high the auto-approval level is set. Gate correction: the earlier
lane docs' "flag disables the permission-check layer" wording is wrong; see above.

### `--skip-permissions-unsafe`, recovered semantics (yes)

Autonomy tiers off/low/medium/high are enforced via `getRequiredAutonomyLevel`
(`src/agent/autonomy.ts:22-53`); org policy can cap the max level
(`requireAllowedAutonomyMode`, `settings.general.maxAutonomyLevel`).

### permissionRules, declarative rule layer (settings)

`permissionRules` is a declarative `{version, rules}` allow/ask/block layer,
`PERMISSION_RULES_CONFIG_VERSION = 1` (`CommandPolicyEngine.ts:108-136`).

### Whole-process sandbox

Guard FD (`src/sandbox/constants.ts:9-18`: "Possession of the fd (not any string value) is
the capability") plus child-env scrubbing of `DROID_WHOLE_PROCESS_SANDBOX_*`
(`src/sandbox/env.ts`).

## 5. Internal notes and hidden flags

- **Bundled internal QA skill `dogfood`**: Factory's own "systematically explore a web app"
  workflow, shipped to every user (skill asset @282223838), driving the Rust `agent-browser`
  binary (true extent 14,251,979 B, source-gated; the earlier 28.5 MB figure was a segment-map
  artifact - dated erratum filed).
- **`droid dataset`** (hidden, `AutoEvalPipeline`-gated): Factory-internal eval-dataset
  authoring (`src/entrypoints/dataset/command.ts`). **`droid experiments`** (hidden,
  `ExperimentLedger`-gated, `/api/v0/experiments`): experiment ledger authoring. Both are
  Factory-internal tooling shipped in the public binary.
- `permissionRules`: declarative `{version, rules}` allow/ask/block layer (see §3 above).
- Config roots: `~/.factory/`, project `.factory/`; auth at `~/.factory/auth.json`.

### User-stats, badges and the hidden dataset plus experiments entrypoints (closure wave, 2026-10-20)

**user-stats badges** (`packages/runtime/user-stats/`): computed locally only - tiered badges
on sessions, streaks, focused time; **zero network** from that surface (closure wave).

## 6. Daemon internals and e2e hooks (wave 3)

**167 distinct `daemon.*` RPC methods** (source census: 132 `*Method` enums + 8 `*Event` enums +
27 dotted-subnamespace). **Act-as grants are backend-minted** (`fdg-<id>-<secret>`, 5-minute
TTL; daemon verifies via `POST /api/v0/act-as-grants/verify`) - the CLI never mints them
(gate correction of the earlier "client-minted" claim). Act-as targets service-account-owned
daemons only; prem daemons reject grants. Dangerous-subset inventory includes terminal access,
SSH-key installation, proxy tokens, MCP credentials, git push/PR creation, and session message
injection. `droid daemon --remote-control` runs through the relay.

## 2. HOW IT WAS FOUND

Config lane (env census + permission archaeology), wave-3 daemon RPC census, closure wave
(user-stats, dataset/experiments), gate re-derivation against recovered source.

## 3. WHAT IT UNLOCKS

A user running `--skip-permissions-unsafe` has weaker protection than the flag name suggests -
and stronger than the binary's own error text implies (the blocklist still fires). Any org
admin or power user can enumerate the exact grant surface, the hidden entrypoints, and the
fault-injection hooks available to a process that executes this binary.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Audit the daemon grant surface before enabling remote-control on shared machines.
2. Read `shouldConfirmExecution.ts` for the exact auto-approval ladder before scripting
   `--auto` runs.
3. The E2E hooks are your free fault-injection harness for agent CI.
