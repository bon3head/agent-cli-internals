# 08. Telemetry is two pipelines, not one

**Version pin:** all string evidence from the **0.155.1** bun binary (`otel/src/provider.rs`
etc.), cross-checked against official docs (`https://developers.openai.com/codex/config-advanced/`,
fetched 2026-10-18; docs may describe a newer build than the binary: binary-string
corroboration noted per claim). `codex --help` / `codex exec --help` grep re-verified live
on **0.149.0** (zero matches for `analytic|otel|metric|telemetry`). Exact OTel batch/export
numerics are UNKNOWN; `service.name` value unrecovered.

## 1. WHAT WAS FOUND

**Pipeline 1 (Analytics): ON by default.** Sends anonymous usage/health metrics to OpenAI.
Byte-exact literal in `otel/src/provider.rs` rodata: `"https://ab.chatgpt.com/otlp/v1/metrics"`.
It is the only fully-qualified OTLP URL in the binary (no `/v1/traces` or `/v1/logs` variant:
searched, zero hits). Pipeline attribution (analytics metrics leg) is high-confidence
INFERENCE from placement + docs ("This also disables custom OTLP metrics exporters in Codex
CLI" under `[analytics] enabled = false`); the literal itself is CONFIRMED.
- Per-turn payload includes `codex.turn.cost_microusd` and `codex.turn.token_usage`.
- Metric names (CONFIRMED literals): `codex.api_request`, `codex.api_request.duration_ms`,
  `codex.sse_event`, `codex.tool.call`, `codex.tool.call.duration_ms`,
  `codex.turn.ttft.duration_ms`, `codex.turn.ttfm.duration_ms`, `codex.turn.cost_microusd`,
  `codex.turn.token_usage`, `codex.conversation.turn.count`, `codex.websocket.request.duration_ms`,
  `codex.websocket.event.duration_ms`, `codex.responses_api_overhead.duration_ms`,
  `codex.responses_api_inference_time.duration_ms`, `codex.responses_api_engine_*_ttft/tbt.duration_ms`,
  `codex.sqlite.init.count`, `codex.sqlite.init.duration_ms`.
- Default metric tags (docs + binary): `auth_mode`, `originator`, `session_source`, `model`, `app.version`; `originator` values `cli`, `vscode`, `vscode-insiders`, `cursor`.
- **Kill switch:** `[analytics] enabled = false` in config.toml (single-field
  `AnalyticsConfigToml`; help text quotes the exact TOML block). No CLI flag exists:
  `codex --help` and `codex exec --help` contain zero matches for telemetry terms (verified
  0.149.0). Also settable via `-c analytics.enabled=false`.

**Pipeline 2 (OTel): OFF by default, opt-in.** `[otel]` config with `environment`
(defaults `"dev"`), `log_user_prompt` (default false: prompts redacted unless enabled),
`exporter` (only two variants: `otlp-http` / `otlp-grpc`; `exporter = "none"` maps to the
enum being unset), `trace_exporter`, `span_attributes`, TLS sub-config
(`ca-certificate`, `client-certificate`, `client-private-key`, kebab-case). Linked
opentelemetry-otlp 0.31.0 honors the standard env overrides (CONFIRMED literals):
`OTEL_EXPORTER_OTLP_{ENDPOINT,TRACES_ENDPOINT,METRICS_ENDPOINT,LOGS_ENDPOINT,HEADERS,TIMEOUT}`,
per-signal timeout/headers/compression vars, `OTEL_BSP_*` / `OTEL_BLRP_*` batch vars,
`OTEL_METRIC_EXPORT_INTERVAL`, `OTEL_TRACES_SAMPLER{,_ARG}`. **No opt-out is needed: it
sends nothing unless configured** (`"No OTEL exporter enabled in settings."`). Note:
`[analytics] enabled = false` additionally disables *custom OTel metrics exporters*; whether
it also disables OTel *log* export is UNVERIFIED (docs scope it to analytics + metrics).

**Two kill-switch gotchas (CONFIRMED):**
1. `OTEL_SDK_DISABLED` has **zero hits** in the binary: the env var operators reach for
   first silently does nothing here (absence-of-string; strong but not absolute proof).
2. A prior pass's "no opt-out found" was imprecise and is corrected here: OTel needs no
   opt-out (it's opt-in); analytics is the pipeline needing the opt-out.

**Payload shapes (CONFIRMED literals):** structured OTel log events:
`codex.conversation_starts`, `codex.api_request`, `codex.sse_event`, `codex.websocket_request`,
`codex.user_prompt`, `codex.tool_decision`, `codex.tool_result`, `codex.websocket.event`,
`codex.process.start`, `codex.app_server.otel_reloaded`; instrumentation scopes
`codex_api`, `codex_client`, `codex_core`, `codex_mcp`, `codex_http_client`,
`codex_network_proxy`, `codex_otel.trace_safe` vs `codex_otel.log_only` (deliberate
trace-safe vs log-only split), `codex_exec_server`, `codex_otel` launch trace fields
`launch.trace_id`/`launch.span_id`. Trace machinery: `tracing-opentelemetry-0.32.1`
bridge, `BatchSpanProcessor`, `HttpTracesClient`/`TonicTracesClient`; exporters batch
asynchronously and flush on shutdown (`codex-otel-shutdown` channel). Resource attributes:
`service.name`, `service.version`, `env`, `host.name` (keys confirmed; `service.name`
*value* unrecovered). SDK fallback defaults `http://localhost:4318` (HTTP) /
`http://localhost:4317` (gRPC) present as literals.

**Scope (CONFIRMED):** telemetry is process-wide infrastructure shared by all surfaces.
app-server installs and hot-reloads exporters (`app-server/src/otel_reloader.rs`,
`"reloaded telemetry exporters after account change"`); exec-server has its own module
(`cli/src/exec_server_telemetry.rs`); TUI and `exec` both emit via `codex_core`. MCP *tool
calls* are instrumented (`codex_mcp` scope). A process-wide SQLite telemetry sink has a
duplicate-install guard (`state/src/telemetry.rs:41`). There is no `mcp-server`
subcommand in this build (`mcp` = "Manage external MCP servers").

Also shipped: a Statsig **client key** literal immediately after the metrics URL in rodata
(`"client-MkRuleRQBd6qakfnDYqJVR9JuXcY57Ljly3vi5JVUIO"`: client keys are public-by-design;
quoted as evidence only) plus a `"statsig exporter should be resolved"` unreachable-code
string proving a Statsig-exporter code path exists in the provider.

**CONFIRMED vs INFERENCE:** two-pipeline split, both defaults, endpoint literal, config
keys, kill switch, event/metric names, opt-in/opt-out directions, and the
`OTEL_SDK_DISABLED` absence are CONFIRMED. Which pipeline consumes the ab.chatgpt.com URL
is high-confidence INFERENCE. Batch numerics, `service.name` value, and remaining
`OtelConfigToml` fields are UNKNOWN.

## 2. HOW IT WAS FOUND

Lane E (telemetry): `strings -a` + byte-offset reads of the 0.155.1 binary; claim/quote/proves
structure for every literal (each claim records what the quote proves and what it doesn't);
docs cross-check; `codex --help` / `codex exec --help` greps re-verified on 0.149.0 in
trials. Correction history: the earlier pass's "no opt-out found" was imprecise and was
fixed by distinguishing the two pipelines.

## 3. WHAT IT UNLOCKS

You can audit and control exactly what Codex phones home: the default-on analytics stream
(cost, token usage, health) has a documented config kill switch, while the rich OTel
stream (per-request traces, tool decisions, prompts) is yours to opt into and point at
your own collector. Knowing `OTEL_SDK_DISABLED` is a no-op prevents a false sense of
compliance. For teams, the per-turn `cost_microusd` metric is a ready-made billing feed.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Disable default analytics: add to `~/.codex/config.toml`:
   ```toml
   [analytics]
   enabled = false
   ```
   or pass `-c analytics.enabled=false`. (Do NOT rely on `OTEL_SDK_DISABLED=true`: it is unreferenced.)
2. Opt into your own OTel pipeline:
   ```toml
   [otel]
   environment = "prod"
   log_user_prompt = false        # redact prompts (default)
   exporter = { otlp-http = { endpoint = "https://otel.internal/v1/logs", protocol = "binary", headers = { "x-otlp-api-key" = "${OTLP_TOKEN}" } } }
   ```
   or `otlp-grpc` with `endpoint = "https://otel.internal:4317"`. Standard
   `OTEL_EXPORTER_OTLP_*` env vars also honored; mTLS via the `ca-certificate` /
   `client-certificate` / `client-private-key` sub-config.
3. Note the `[analytics] enabled = false` also kills custom OTel *metrics* exporters:
   keep it in mind if you want your own metrics pipeline alongside analytics disabled.
4. In the app-server, exporters hot-reload on account change (`codex.app_server.otel_reloaded`
   event): no restart needed after auth changes.
5. Build dashboards off `codex.turn.cost_microusd` and `codex.turn.token_usage` per turn,
   tagged by `model`, `auth_mode`, `originator`.
