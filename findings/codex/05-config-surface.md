# 05. Config: 101 of 101 fields recovered, 10-layer precedence

> **Correction (2026-10-19, reinforcement):** the "97 of 101" figure is withdrawn — the true
> figure is **101/101**, recovered from the actual serde `FIELDS: &[&str]` statics (101 consecutive
> `(ptr,len)` pairs @0xfcc98c0, byte-identical duplicate @0xfe370d0). Of the prior's 97: 82 correct
> in order, 15 misattributed to other structs, 16 true fields missed. **`sprofile` never existed**
> — it was `js_repl_node_module_dirs` + `profile` + `profiles` misread at ptr level (claim killed).
> Precedence corrections: `sessionFlags` ≡ the `-c` layer (prior double-counted); `legacyManaged`
> loads topmost per the schema description, not 5th; only 7/10 layer-name strings verify
> (`user`/`system`/`profile` unattributable).

**Version pin:** field list recovered from the **0.155.1** bun binary (serde `FIELDS`
literals; config-surface.md §1–2). Trials did not regenerate config strings against
0.149.0, so per-key availability on 0.149.0 is UNCONFIRMED where it matters: spot-check
before relying on a specific key.

## 1. WHAT WAS FOUND

- **`struct ConfigToml with 101 elements`; all 101 recovered** in declaration order from the
  serde `FIELDS: &[&str]` statics (101 consecutive `(ptr,len)` pairs @0xfcc98c0, byte-identical
  duplicate @0xfe370d0): the correct method; packed-string-run tokenizing was lossy (see
  correction note above).
- **10-layer precedence, lowest → highest:** packagedDefaults → mdm → system →
  enterpriseManaged → legacyManaged → user (`~/.codex/config.toml`, repointable via
  `CODEX_HOME`) → profile (`-p`) → project → sessionFlags → `-c key=value` dotted
  overrides. (Sources: `ConfigLayerSource` enum in the 0.149.0 app-server schema + CLI help.)
- Key recovered fields (0.155.1; defaults UNCONFIRMED for ~90 of 101):
  - `model`, `review_model`, `model_provider`, `model_context_window`
  - `sandbox`, `approval_policy`, `approvals_reviewer` (`user | auto_review | guardian_subagent`: CONFIRMED schema enum; `guardian_subagent` is the legacy name per the schema description, `auto_review` is current: "a carefully prompted subagent to gather relevant context and apply a risk-based decision framework before approving or denying the request")
  - `[model_providers.<name>]`: `base_url`, `env_key`, `wire_api`, `env_http_headers`, `query_params`, retry/timeout knobs, `requires_openai_auth`, `supports_websockets`, `supports_standalone_web_search`, `aws`… (`ModelProviderInfo` 18 elements, 12/18 recovered)
  - `[mcp_servers.*]`: per-server `RawMcpServerConfig` (28 fields; see Finding 09)
  - `[shell_environment_policy]` 7/7: `inherit`, `ignore_default_excludes`, `set`, `include_only`, `filters`, `max_depth`, `experimental_use_profile`
  - `[browser_use]` 3/3, `[computer_use]` 3/3, `[memories]` 13/14, `[network]` 10/13, `[otel]` 2/8 (`environment`, `log_user_prompt`; see Finding 08)
  - Full `[tui]` keymaps (`tui.chat`, `tui.pager`, `tui.agents`, `tui.editor`, `tui.global`, `tui.composer`, `tui.vim_normal`, `tui.vim_operator`, `tui.vim_search`, `tui.vim_text_object`, `tui.approval`)
  - `[analytics]` single field: `enabled` → the telemetry kill switch (Finding 08)
- **Custom providers are real:** `[model_providers.<name>]` with `base_url` + `env_key` +
  `wire_api` lets Codex talk to non-OpenAI endpoints (OpenAI-Responses-compatible or
  others per `wire_api`).
- **`--strict-config`**: promotes unknown config fields to hard errors (otherwise the
  app-server emits a `ConfigWarningNotification` with path + line/column).
- **`codex features enable|disable <name>`** writes the flag into config.toml persistently;
  `--enable <FEATURE>` ≡ `-c features.<name>=true`.
- Roadmap structs exist but fields unrecovered: `TokenBudgetConfigToml`,
  rollout-budget, multi-agent v2, guardian v2, network-proxy config (existence CONFIRMED,
  fields UNKNOWN).
- Bonus eureka (0.149.0 schema): the app-server schema embeds the typed *resolved* config;
  `ConfigReadResponse.json` carries verbatim enums and defaults (e.g. `WebSearchMode:
  [disabled, cached, indexed, live]`).

**CONFIRMED vs INFERENCE:** the 101-field inventory, the 10-layer order, and per-section
field lists are CONFIRMED from binary strings + schema + help. Per-key *defaults* are
UNCONFIRMED for ~90 keys (defaults were not found as literals).

## 2. HOW IT WAS FOUND

Lane B (config-surface), 0.155.1 bun binary. Method: dumped `strings`, located packed
serde `FIELDS` literals, split them into ordered runs, validated each run against the
`struct ConfigToml with 101 elements` count and cross-checked adjacency pairs (e.g.
`model` next to `review_model`). Cross-validated against `codex --help` / `codex exec
--help` text (e.g. `-c model="o3"` example, `-c shell_environment_policy.inherit=all`
example), the live `~/.codex/config.toml` on this box (`[projects."/home/hatch"]
trust_level = "trusted"`), and `~/workspace/rea-codex/app-server-schema/v2/ConfigReadResponse.json`.

## 3. WHAT IT UNLOCKS

Codex is not a take-it-or-leave-it binary: nearly every behavior (model, sandbox,
approval policy, MCP servers, per-project trust, telemetry, shell env inheritance, TUI
keymaps, custom model providers) is a config knob with a predictable override order.
Enterprise admins get MDM/enterprise layers; developers get `-c` one-shot overrides; the
app-server can read and hot-write config at runtime. And with `[model_providers.*]` you can
point the whole agent apparatus at your own inference endpoint.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Read effective config at runtime: `config/read` (optionally `includeLayers: true`,
   `cwd` to resolve project layers): the response is the typed resolved config.
2. Hot-edit without restart: `config/value/write{keyPath, value, mergeStrategy}` or
   `config/batchWrite{edits}` with `reloadUserConfig: true` to hot-reload into loaded
   threads (note: model/effort/tier/personality defaults are NOT reloaded; documented).
3. Dotted overrides from the CLI: `-c model="gpt-5.6-terra"`, `-c
   'shell_environment_policy.inherit=all'`; the value is parsed as TOML, falling back to a
   raw string.
4. Point at a custom provider:
   ```toml
   [model_providers.my-proxy]
   base_url = "https://proxy.internal/v1"
   env_key = "MY_PROXY_KEY"
   wire_api = "responses"
   ```
   then `-c model_provider="my-proxy"` (0.155.1-verified fields; confirm on your build).
5. Ship safe defaults: run with `--strict-config` in CI/driver harnesses so a typo'd key
   fails loudly instead of being silently ignored.
6. Kill default-on telemetry: `[analytics] enabled = false` (Finding 08). Repoint home:
   `CODEX_HOME=/custom/dir` (60 string occurrences); skip user config in exec with
   `--ignore-user-config`.
