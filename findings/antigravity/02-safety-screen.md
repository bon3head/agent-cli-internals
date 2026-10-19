# 02. Safety screen decoded: per-step, 2-stage, server-overridable

**Trial status:** CONFIRMED. String spot-checks re-ran clean: `sir_flash_lite` at strings line 1604502; assembled config header at ~1611061 (byte-for-byte the line quoted in the lane eureka). `AGY_CLI_DISABLE_SAFETY_FILTERING` string found (1 hit). Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

The binary embeds a fully assembled, ready-to-parse safety-monitor config (CONFIRMED):

```
# Source: per_monitor/*/ + profiles/antigravity.textproto
# Regenerate: blaze run //gdm/security/agi_control/agent_monitoring/monitors/config:assemble -- --profile=profiles/antigravity.textproto
# Checksum: sha256:caeb48770b7a4df5d910608adeeacb73441f9ddf5e273ee61a11cd5676f5342f
# proto-message: MonitorsConfig
```

Decoded to `deep-dive/monitors-config.txt` (30KB). Three monitors, all `enabled: true`, all `EXECUTION_PHASE_PRE_TOOL`: they run on **every tool-call step, before execution**:

| monitor | mode | tier | thinking | tokens | timeout |
|---|---|---|---|---|---|
| `agy_tool_safety` | LOG | heuristic allowlist | n/a | n/a | 1s |
| `sir_flash_lite` | LOG | MODEL_TIER_FLASH_LITE | MINIMAL | 16k | 8s |
| `severe_internal_risks_agy` | BLOCK | MODEL_TIER_FLASH | LOW | 100k | 8s |

Pipeline: flash-lite triage watches the latest step and decides whether to escalate → flash reviewer applies the embedded **10.7KB severe-internal-risks rubric** → BLOCK mode stops the step. Triage prompt (byte-exact): "You are a safety pre-filter overseeing an AI coding agent..."

Server control (CONFIRMED): `agent_monitoring.externalMonitorConfigManager` + error strings `failed to parse embedded config: %w` / `failed to unmarshal monitors config: %w`; the embedded config is a stale fallback; live config is pushed remotely. Monitor taxonomy (`gdm/security/agi_control`) carries staged-rollout machinery (`GetUserGroups`, `GetExcludedUserGroups`, `GetExperiment`): Google can roll safety changes by user group / A-B without a client release (machinery present, no observed instance; INFERENCE on actual use).

Observability: invocation logs `LLM Monitor %s: Calling LLM (model: %s)` and `Logprob Monitor %s: Starting evaluation` are visible in verbose output.

Also CONFIRMED: URL/tool vetting via PolicyGuardian + GAVS antivirus: `[PolicyGuardian] Checking URL with GAVS: %s` / `Destination URL flagged by antivirus scan: %s`.

**Open:** `AGY_CLI_DISABLE_SAFETY_FILTERING` exists as a string; whether `os.Getenv` actually reads it is UNVERIFIED (behavioral probe needed).

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A5 (internal intel), strings tier. The eureka (~02:05, 2026-10-19): a grep for monitor strings landed on the assembled-config blob at strings :1611062 with the blaze regenerate command and sha256 checksum in its header. Decoded and saved to `deep-dive/monitors-config.txt`. Trial re-verified with `grep -n 'name: "sir_flash_lite"' .../agy.strings` → line 1604502 and `sed -n 1611058,1611070p` → the header byte-for-byte.

---

## 3. WHAT IT UNLOCKS

Every single thing the agent does, every tool call, passes a hidden two-stage safety review before it runs: a fast cheap model triages the step, and a stronger model with a ten-thousand-word rulebook can block it outright. Google can also change that rulebook on your machine remotely, without shipping a new version of the CLI. Knowing the exact config means you know what triggers the reviewer, that the fallback copy lives inside the binary, and that verbose logs will show you every monitor invocation.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Read the rubric:** the 10.7KB `severe_internal_risks_agy` rubric is extractable from rodata around strings :1611061; it is the exact blocking criteria. Parse it to know which tool calls will be blocked.
- **Observe invocations:** run with verbose output and grep for `LLM Monitor ... Calling LLM (model: ...)`: tells you per step which monitor fired and which model it used.
- **Server override path:** symbol `agent_monitoring.externalMonitorConfigManager`: live config push path; the embedded copy is fallback. `LanguageServerService.SetMendelFlagOverrides` exists but `Mendel flag overrides require developer mode` (`LanguageServerConfig.GetDevMode`).
- **Disable candidate (UNVERIFIED):** `AGY_CLI_DISABLE_SAFETY_FILTERING` string present (:346639). Behavioral probe needed: run with the env var set and a policy-triggering step, observe whether monitor log lines disappear.
- Taxonomy for custom monitors: `google3/gdm/security/agi_control/agent_monitoring/monitors/monitor_config_go_proto`; 10 monitor types (`HeuristicSafetyMonitor`, `LlmMonitor`, `LogprobMonitor`, `EmbeddingMonitor`, `IntrospectionVerdictsMonitor`, `PolicyGuardianMonitor`, `AcsvMonitor`, `AgcisMonitor`, `AgcisReasoningMonitor`), modes LOG/BLOCK, `EXECUTION_PHASE_PRE_TOOL`.
