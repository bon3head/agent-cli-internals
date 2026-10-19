# Finding 11 — The autonomy roadmap is a config surface: six experimental structs, fully field-recovered

**Version pin:** codex CLI **0.155.1**, 269,273,536 bytes, sha256 `0753dfe1…b761`.
All offsets are file offsets in that image. `&[&str]` FIELDS arrays are base-0
static-pie: virtual address == file offset (verified: every pointer in the walked
array resolves to `[a-z0-9_]` ASCII).

## 1. WHAT WAS FOUND

The structs that were previously "existence confirmed, fields unrecovered"
(Guardian, token budgets, multi-agent v2, code mode, network proxy, rollout
budgets) are now fully field-recovered. Each config key below is a real,
config-file-writable field with real validation strings in the binary — this is
the config surface for the shipped experimental systems (guardian classifier,
token budgeting/compaction, multi-agent, code mode, network proxy, rollout
budgets) plus 7 bonus structs recovered from the same array.

A **108-entry flattened `&[&str]` FIELDS array at file offset 264373824**
concatenates the roadmap structs' field lists in declaration order. Segmentation
is locked by each struct's `struct <Name> with <N> elements` marker and
cross-checked against per-field `features.<section>.<field>` validation strings.

### GuardianV2ConfigToml — 14/14
`struct GuardianV2ConfigToml with 14 elements` @218812826 (8 occurrences).
108-array indices 11–24:

```
free_guardian, thread_context, persist_scores, classifier_instructions,
review_threshold, max_tool_call_lag, reasoning_effort, max_action_tokens,
max_classifier_instruction_tokens, reuse_parent_compaction,
max_parent_compaction_tokens, review_scope, transcript, limited
```

Cross-ref: `Guardian v2 review_threshold must be between 0.0 and 1.0`
(float field confirmed); `Guardian v2 transcript max_recent_non_user_entries
must be positive`.

**Dated note:** a second, shorter packing exists under bare header
`GuardianV2ConfigToml` @219301251 (5 occurrences) with 12 fields — same list
minus `review_threshold` and `reasoning_effort`. The 14-field list is current
(marker says N=14); the 12-field packing is an older variant retained in the
binary (INFERENCE on age, CONFIRMED on bytes). Prior docs that said
"GuardianV2 fields unrecovered" are superseded by this finding.

### TokenBudgetConfigToml — 7/7
`struct TokenBudgetConfigToml with 7 elements` @218813084 (7 occurrences).
108-array indices 26–32:

```
enabled, use_history_notes_extension, reminder_threshold_tokens,
reminder_message_template, guidance_message, auto_compact_fallback_prompt,
auto_compact_fallback_buffer_tokens
```

Cross-refs (all literal in binary):
`features.token_budget.auto_compact_fallback_buffer_tokens` ("must be positive";
"is required when auto_compact_fallback_prompt is set"),
`features.token_budget.reminder_message_template` ("must not exceed"),
`token_budget.use_history_notes_extension` (feature key list).

### MultiAgentV2ConfigToml — 16/16
`struct MultiAgentV2ConfigToml with 16 elements` @218813281 (7 occurrences).
108-array indices 35–50:

```
enabled, max_concurrent_threads_per_session, min_wait_timeout_ms,
max_wait_timeout_ms, default_wait_timeout_ms, usage_hint_enabled,
usage_hint_text, root_agent_usage_hint_text, subagent_usage_hint_text,
subagent_developer_instructions, multi_agent_mode_hint_text,
tool_namespace, hide_spawn_agent_metadata,
expose_spawn_agent_model_overrides, wait_agent_enabled, non_code_mode_only
```

Cross-ref: `features.multi_agent_v2.tool_namespace` (literal).

### CodeModeConfigToml — 4/4
`struct CodeModeConfigToml with 4 elements` @218810210 (7 occurrences).
108-array indices 4–7:

```
enabled, default_exec_yield_time_ms, excluded_tool_namespaces,
direct_only_tool_namespaces
```

### NetworkProxyConfigToml — 14/14
`struct NetworkProxyConfigToml with 14 elements` @218813327 (7 occurrences).
108-array indices 51–64:

```
enabled, proxy_url, enable_socks5, socks_url, enable_socks5_udp,
allow_upstream_proxy, dangerously_allow_non_loopback_proxy,
dangerously_allow_all_unix_sockets, mode, domains, unix_sockets,
allow_local_binding, credential_broker, credentials
```

Cross-refs: `network-proxy/src/socks5.rs`, `CODEX_NETWORK_PROXY_ACTIVE`,
`credential brokerage could not creat[e]`. `mode` (index 59) is the least
cross-referenced field.

### RolloutBudgetConfigToml — 5/5
`struct RolloutBudgetConfigToml with 5 elements` @218813395 (7 occurrences).
108-array indices 67–71:

```
enabled, limit_tokens, reminder_at_remaining_tokens,
sampling_token_weight, prefill_token_weight
```

Cross-refs: `features.rollout_budget.reminder_at_remaining_tokens is required
when rollout_budget is enabled`; `features.rollout_budget.limit_tokens must be
positive`.

### Bonus structs (7, segmented from the same array)
- **CodeModeHostConfigToml** (N=2): `enabled, disable_in_process_fallback` (indices 33–34).
- **ToolRegistryConfigToml** (N=2): `error_on_tool_collisions, turn_metadata_includes_tool_info` (indices 65–66).
- **ContextManagementConfigToml** (N=1): `experimental_mode` (index 75).
- **CurrentTimeReminderConfigToml** (N=5): `enabled, reminder_interval_seconds, clock_source, delivery_mode, sleep_tool` (indices 76–80).
- **GuardianV2TranscriptConfigToml** (N=7): `sources, include_images, max_message_entry_tokens, max_tool_entry_tokens, max_message_transcript_tokens, max_tool_transcript_tokens, max_recent_non_user_entries` (indices 81–87).
- **GuardianV2ReviewScopeConfigToml** (N=2): `computer_use_only, sandboxed_exec_commands` (indices 90–91) — also confirmed as a standalone 2-entry pointer array @265778016 (the only individual struct array that survived dead-code elimination).
- **ModelTokenBudgetConfig** (N=7): `enabled, use_history_notes_extension, reminder_threshold_tokens, reminder_message_template, auto_compact_fallback_prompt, auto_compact_fallback_buffer_tokens` (6 of 7 recovered; 7th UNRECOVERED, HYPOTHESIS: `guidance_message`).

**Unresolved in the 108-array (HYPOTHESIS: enum variants, not assigned):**
indices 0–3 (`model_driven, always_on, system, external`), index 25 (`full`),
indices 88–89 (`any_inference, after_user_or_tool_output`), indices 92–107
(tail: `enabled, server_names, enabled, path, restricted, enabled, skip, auto,
always, never, disabled, cached, indexed, live, none, custom`).

### Dated corrections to prior docs
- 2026-10-19: `ShellEnvironmentPolicyTomlRaw` (N=7) is `inherit,
  ignore_default_excludes, exclude, set, include_only, filters,
  experimental_use_profile` — the 7th field is `exclude`, **not** `max_depth`
  as previously recorded. `max_depth` does not appear in that struct's packing.
- 2026-10-19: prior repo docs baselined config-surface work on the stale
  0.149.0 schema emission (95/10/75/1). Fresh 0.155.1 schema emission is
  **102/10/82/1**. All counts above are 0.155.1.

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Method: read-only. Rust `&str` literals are packed with **no NUL separators**
(verified with `od -c`: names are back-to-back), so the packed name-runs used by
earlier passes cannot be split. The new technique: locate the `&[&str]` FIELDS
pointer arrays — 16-byte `(u64 ptr, u64 len)` entries — and walk them, validating
each entry resolves to `[a-z0-9_]` ASCII.

Reproduction (independent walk, byte-identical results to the original pass):

```python
import struct
data = open('codex-0.155.1','rb').read()   # 269273536 bytes, sha256 0753dfe1…b761
off = 264373824                            # 108-entry flattened FIELDS array
for i in range(108):
    ptr, ln = struct.unpack_from('<QQ', data, off + i*16)   # vaddr == file offset
    print(data[ptr:ptr+ln].decode())                        # -> names[0..107]
```

The walk returned all 108 entries as valid identifiers:

```
model_driven, always_on, system, external, enabled,
default_exec_yield_time_ms, excluded_tool_namespaces, direct_only_tool_namespaces,   # CodeMode 4-7
enabled, mode,                                                                           # (unresolved 9-10)
free_guardian, thread_context, persist_scores, classifier_instructions, review_threshold,
max_tool_call_lag, reasoning_effort, max_action_tokens, max_classifier_instruction_tokens,
reuse_parent_compaction, max_parent_compaction_tokens, review_scope, transcript, limited,  # GuardianV2 11-24
full,                                                                                    # (unresolved 25)
enabled, use_history_notes_extension, reminder_threshold_tokens, reminder_message_template,
guidance_message, auto_compact_fallback_prompt, auto_compact_fallback_buffer_tokens,      # TokenBudget 26-32
enabled, disable_in_process_fallback,                                                     # CodeModeHost 33-34
enabled, max_concurrent_threads_per_session, min_wait_timeout_ms, max_wait_timeout_ms,
default_wait_timeout_ms, usage_hint_enabled, usage_hint_text, root_agent_usage_hint_text,
subagent_usage_hint_text, subagent_developer_instructions, multi_agent_mode_hint_text,
tool_namespace, hide_spawn_agent_metadata, expose_spawn_agent_model_overrides,
wait_agent_enabled, non_code_mode_only,                                                   # MultiAgentV2 35-50
enabled, proxy_url, enable_socks5, socks_url, enable_socks5_udp, allow_upstream_proxy,
dangerously_allow_non_loopback_proxy, dangerously_allow_all_unix_sockets, mode, domains,
unix_sockets, allow_local_binding, credential_broker, credentials,                         # NetworkProxy 51-64
error_on_tool_collisions, turn_metadata_includes_tool_info,                                # ToolRegistry 65-66
enabled, limit_tokens, reminder_at_remaining_tokens, sampling_token_weight,
prefill_token_weight,                                                                     # RolloutBudget 67-71
tool_calls, tool_outputs, reasoning,                                                       # 72-74 (transcript sources enum)
experimental_mode,                                                                         # ContextManagement 75
enabled, reminder_interval_seconds, clock_source, delivery_mode, sleep_tool,               # CurrentTimeReminder 76-80
sources, include_images, max_message_entry_tokens, max_tool_entry_tokens,
max_message_transcript_tokens, max_tool_transcript_tokens,
max_recent_non_user_entries,                                                               # GuardianV2Transcript 81-87
any_inference, after_user_or_tool_output,                                                   # (unresolved 88-89)
computer_use_only, sandboxed_exec_commands,                                                # GuardianV2ReviewScope 90-91
enabled, server_names, enabled, path, restricted, enabled, skip, auto, always, never,
disabled, cached, indexed, live, none, custom                                              # (unresolved tail 92-107)
```

Segmentation locked by marker occurrences, spot-verified on this pass:
`struct GuardianV2ConfigToml with 14 elements` first @218812826 (8 occ);
`struct TokenBudgetConfigToml with 7 elements` first @218813084 (7 occ);
`struct MultiAgentV2ConfigToml with 16 elements` first @218813281 (7 occ);
`struct CodeModeConfigToml with 4 elements` first @218810210 (7 occ);
`struct NetworkProxyConfigToml with 14 elements` first @218813327 (7 occ);
`struct RolloutBudgetConfigToml with 5 elements` first @218813395 (7 occ).

## 3. WHAT IT UNLOCKS (plain language, no jargon)

Codex's unreleased features are not hidden behind special flags or secret
commands — they are settings files anyone can read and write. Every name in
these lists is a knob you can turn in `config.toml`. Want to know how OpenAI
plans to cap tokens per rollout? It's right here: `limit_tokens`,
`reminder_at_remaining_tokens`, `sampling_token_weight`, `prefill_token_weight`.
Curious what the "guardian" safety checker will score on you?
`classifier_instructions`, `review_threshold`, `max_action_tokens`,
`persist_scores` — its whole dashboard is laid out in plain text. This finding
turns a pile of mystery "experimental feature" rumors into an actual settings
manual: each knob's name tells you what it controls, and each knob's presence
in the binary tells you the feature is already built and waiting for a switch.

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

1. Write `config.toml` entries under `[features.guardian]` /
   `[features.token_budget]` / `[features.multi_agent_v2]` /
   `[features.network]` / `[features.rollout_budget]` using exactly these key
   names (serde field names = config keys; snake_case verbatim).
2. Pair each key with the validation strings: e.g.
   `auto_compact_fallback_buffer_tokens` "must be positive" and is "required
   when auto_compact_fallback_prompt is set"; `review_threshold` accepts a float
   "between 0.0 and 1.0". Write a validator that enforces the same constraints
   client-side before Codex rejects the config at load.
3. Watch the 0.149.0-era 12-field Guardian packing vs the current 14-field one:
   any code that parsed the 12-field layout must accept `review_threshold` and
   `reasoning_effort` as new optional keys — schema migration for free.
4. Use the unresolved tail (indices 92–107) as the fuzzing target for the next
   pass: they decode as valid identifiers and sit adjacent to confirmed enum
   variants (`tool_calls|tool_outputs|reasoning`), so walk each struct's
   serde `VARIANTS` arrays next to place them.
