# Finding 04 — codex-code-mode-host: Rust+V8 cell executor over gRPC or stdio IPC

**Version pin:** strings + `--help` of the host binary at
`~/.bun/install/global/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex-code-mode-host`
(69 MB), which ships with the **0.155.1** main binary. Gate flags from `feature-flags.txt`,
which pins the **0.149.0** inventory (118 flags; 0.155.1 reports 142 — see §1). The 2026-10-09
"Code Mode is unavailable" incident (TOOLS.md) was host-*resolution*, never a flag question.

## 1. WHAT WAS FOUND

`codex-code-mode-host` is **not a JS runtime binary**. It is a Rust binary embedding V8
(rusty_v8, registry stamps `v8-150.4.0/src/isolate.rs`, `V8.rs`, `value_serializer.rs`) that
executes **raw JavaScript "cells"** fed to it by the main `codex` binary — the main side
(`core/src/tools/code_mode/execute_handler.rs`) says it `# expects raw JavaScript source text`.
No `.js` filenames or bootstrap scripts appear in the host's strings: the JS comes from the
wire, and one cell = one V8 context whose state persists across `Execute` calls within a
session.

**Two transports**, selected by the host's `--listen <URL>` (default `stdio`):
- **stdio (default):** length-framed IPC — `code-mode-protocol/src/host/codec.rs` with strings
  `code-mode IPC frame length `, `&failed to encode/decode code-mode IPC frame: `, and
  per-direction size caps (`code-mode initial response exceeds the IPC frame limit: `,
  `code-mode host response exceeds the IPC frame limit: `).
- **gRPC (tonic):** service `codex.code_mode.v1.CodeModeHost` with methods `OpenSession`,
  `CloseSession`, `Execute`, `Wait`, `CancelWait`, `SubscribeToToolCalls`, `CompleteToolCall`,
  `AcknowledgeNotification`, `Terminate`. The host binds HTTP when given `--listen
  grpc://IP:PORT` (`)codex-code-mode-host listening on http://`, tonic
  `TcpConnectInfo` present). The main side also parses `unix://` sockets and http(s) origins
  (`invalid gRPC code-mode Unix socket endpoint: `).

**Handshake (both transports):** `connection/hello` → `connection/ready` (or
`connection/rejected`), with version negotiation and capability sets — `ClientHelloWire`
carries `selected_version`, `supportedVersions`, `requiredCapabilities`,
`optionalCapabilities`; rejections enumerate `noCompatibleVersion`,
`missingRequiredCapability`, `invalidHello`.

**The sandbox is deliberately thin; policy lives in the main binary.** The only
host-provided JS globals found in strings are timers: `setTimeout expects a function
callback`, `clearTimeout expects a numeric timeout id` (no `fetch`, no `console.*`
injection, no `require` — INFERENCE from absence). Tool calls from JS are **delegated back**
to the main process: the client calls `SubscribeToToolCalls` with tool definitions
(`tool_name`, `description`, `input_schema`, `output_schema`, `tool_kind`); JS emits
`tool/invoke`; the main process executes and returns `tool/result`/`CompleteToolCall`.

**Cooperative async:** execution state machine `Pending → Yielded → Completed | Terminated`;
`WireWaitRequest{cell_id, yield_time_ms}` — a cell can yield and the client blocks on `Wait`
until resume/completion, which is how long-running JS meets the turn loop (INFERENCE, from
`cell_actor` states + `core/src/tools/code_mode/wait_handler.rs`: "Waits on a yielded `-`
cell and returns new output or completion."). Cells can also produce multimodal content
(`input_text`, `input_image`, `image_url`, `input_audio`, `audio_url`). The main side sets
the V8 heap cap (`maxHeapSizeBytes` in the hello/config payload).

**Remote-host wiring:** `--code-mode-host <URL>` on `codex app-server` ("Connect to a
remote code-mode host instead of starting a local host") or config `code_mode_host`
(env `CODE_MODE_HOST` per the config schema). Selection chain: CLI flag > config/env >
local spawn of the bundled host. (Precedence INFERENCE: the flag is documented as "instead
of starting a local host"; flag-over-config follows the usual `-c`/env convention.)

**Feature gates** (0.149.0 flag inventory; 0.155.1 adds ~24 more flags so names may have moved):

| flag | stage / state | gates |
|---|---|---|
| `code_mode` | under development / false | **the whole capability** — tools in `core/src/tools/code_mode/` are inert without it; user error: `Code Mode is unavailable because {reason}; enable 'features.code_mode_host' and install 'codex-code-mode-host'.` |
| `code_mode_host` | stable / true | whether the main binary may use the host; binary resolved via the managed-install manifest (`codex-package.json` entries `codex-code-mode-host`; install roots `/opt/homebrew`, `/usr/local`, `standalone`; `CODEX_MANAGED_BY_{VITE_PLUS,PNPM,NPM,BUN}`) |
| `code_mode_interrupt` | under development / false | interrupt/cancel for running cells (protocol has `delegate/cancel`, `CancelWait`, `operation/cancel`; client-side interrupt behavior gated off) — INFERENCE |
| `code_mode_only` | under development / false | a `tool_mode` value (`direct` | `code_mode_only`) forcing the model's whole tool surface through code-mode cells — INFERENCE |
| `code_mode_buffered_exec` | removed / false | historical execution mode, no longer relevant |

Also present: host OTEL wiring — `--otel-trace-listen` (websocket streaming raw OTLP trace
batches) and `--otel-trace-exporter` (OTLP/HTTP JSON exporter).

**CONFIRMED vs INFERENCE:** Rust+V8 identity, the two transports, the gRPC method list,
handshake message names, delegation model, thin sandbox, V8 heap cap, remote-host flag and
config key, and the flag stages are CONFIRMED from strings + live `--help`. Exact spawner
argv/env for the local launch and the `ClientHello` capability names are UNRECOVERED
(UNKNOWN). Panics are per-task (`code mode tool task panicked`), not per-host — CONFIRMED.

## 2. HOW IT WAS FOUND

Lane D (code-mode-host), strings/schema/behavioral tier only — no disassembly (Ghidra OOMs
on this box), no network, binary unmodified. Verified live:

```
codex-code-mode-host --help        # exits 0; --listen, --otel-trace-listen, --otel-trace-exporter
codex app-server --help            # --code-mode-host <URL>
strings <host> | grep -c 'v8-150'  # registry path stamps
strings <main> <host>              # both embed prost-generated codex.code_mode.v1.rs from
                                   # codex-rs/target/.../codex-code-mode-protocol-362ee48cace341f3/out/
```

Key realization path: the 69MB "host" has no JS bundle in its strings while the *main*
binary holds the tool definitions (`core/src/tools/code_mode/delegate.rs`) — so the
host is an executor and the main binary is the policy brain.

## 3. WHAT IT UNLOCKS

Codex's agent loop is getting a dedicated JavaScript execution engine: instead of the model
calling tools as plain function calls, it can run real JS programs that persist state,
await, and call tools mid-execution — with all policy enforcement staying in the main
binary. Because the host speaks gRPC too, heavy or untrusted JS workloads can be moved to
a separate host (even a remote machine) rather than running beside the agent process.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Standalone experiment: run the bundled host and speak the protocol yourself:
   `codex-code-mode-host --listen grpc://127.0.0.1:50051`, then drive
   `OpenSession` → `SubscribeToToolCalls` (register your tool definitions) → `Execute`
   (raw JS source; `WireExecuteRequest` fields include `enabled_tools`, `source`,
   `max_output_tokens`) → `Wait` for completion → `CompleteToolCall` for each delegated
   `tool/invoke` → `CloseSession`. (Exact field shapes: recover from the shared
   `codex.code_mode.v1.rs` prost definitions; spawner argv and ClientHello capability names
   are UNKNOWN — expect a handshake iteration.)
2. Point an app-server at it: `codex app-server --code-mode-host grpc://127.0.0.1:50051`
   (or `code_mode_host` in config.toml / `CODE_MODE_HOST` env), so Codex spawns no local host.
3. Enable the model-facing surface: `code_mode` is under-development/false in 0.149.0 —
   check `codex features list` on your build; without the flag, code-mode tools are inert.
4. Design for delegation: your client is the tool executor. JS cells can yield (`Wait`),
   so implement long-poll handling on `Wait` rather than assuming `Execute` is synchronous.
5. Observe it: `--otel-trace-listen ws://...` streams raw OTLP trace batches from the host
   independently of the main CLI telemetry (Finding 08).
