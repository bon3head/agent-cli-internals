# 10 — Remote-control mesh + mic-serve + sandbox IPC mapped

**Trial status:** CONFIRMED at suite level (17/17 on the same binary). Port probe: `127.0.0.1:4713` CLOSED at trial time (`agy mic-serve` is a subcommand but nothing is serving). The BOQ/signaling claims were not live-probed (no daemon running; proxy URL is server-driven).

---

## 1. WHAT WAS FOUND

Three remote/local-audio/sandbox surfaces, all loopback or socket based (CONFIRMED, strings tier):

**BOQ ApiService — remote-control signaling plane.** `devtools_jetski_boq_api_proto.ApiService`, 18 real methods: `ConnectInstance`, `ConnectInstanceV2`, `DeleteInstance`, `EvictInstance`, `ForwardProxyCommand`, `InitiateMeshSession`, `ListAuthorizedDevices`, `ListInstances`, `NotifyUser`, `PollSignalingMessages`, `ProxyCommand`, `RecordClientEvent`, `RecordTrajectoryAnalytics`, `RegisterWebPush`, `RevokeAuthorizedDevice`, `SendSignalingMessage`, `StreamProxyCommand`, `UpdateInstance`. Mesh flow: `InitiateMeshSession` → `PollSignalingMessages` / `SendSignalingMessage` → `ProxyCommand` / `StreamProxyCommand` (the v2/streaming variants imply streaming RPCs, consistent with a remote-terminal mesh). **The proxy URL is NOT in the binary** — it comes from the Mendel feature flag `remote-control-proxy-server-url` (strings @24225050: `[RemoteControl] Staying disconnected: remote-control-proxy-server-url Mendel flag not available.`). Daemon installs as systemd unit `agy-remote-control.service` (strings @23114948; launchd/schtasks on other OSes); `--session` = login-scoped instead of boot. CLI: `agy remote-control start [--name] [--session]` | `status` | `stop`. Local daemon state readable via LS `GetRemoteControlInfo`. INFERENCE: the remote drive-a-CLI transport; not directly callable without the server URL.

**mic-serve — microphone loopback server.** `agy mic-serve [--addr]` (default `127.0.0.1:4713`) forwards this machine's mic to a CLI on another host (over SSH port-forward, per changelog @492007). Go package `google3/third_party/jetski/cli/audio/micserve` (`Serve`, `serveConn`). No HTTP routes in strings — raw loopback TCP audio. `ANTIGRAVITY_MIC` env var exists (single occurrence; semantics unknown).

**jetski_connectd.sock — sandbox exec IPC.** Unix socket `/run/user/<uid>/jetski_connectd.sock` (format string, offset ~36196905); plumbed into sidecar/sandbox exec config (`exebox.Config`). INFERENCE: sandbox exec control socket; protocol verbs unenumerated (out of strings tier). Daemon not present on this box.

**MCP child processes:** `agy mcp add|remove|list|enable|disable` (subcommands verified live: `agy mcp --help` → exit 0). Servers spawn as child processes over stdio; OAuth tokens in `mcp_oauth_tokens.json`. No listener of its own — the sanctioned extension path.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A1 (control planes). BOQ method list via deconcat heuristics in `pocs/a1_enumerate_surfaces.py` (full `/...ApiService/Method` path literals confirm methods observed only in concat form, e.g. `EvictInstancetrace`). Remote-control installer strings and the Mendel-flag log line at @24225050. mic-serve package paths from pclntab symbols + changelog @492007. Trial: `timeout 2 bash -c '</dev/tcp/127.0.0.1/4713'` → connection refused (CLOSED); `agy remote-control` present in `agy --help` subcommand list.

---

## 3. WHAT IT UNLOCKS

Beyond the local control plane there is a remote one: the CLI can install a background daemon and join a server-run mesh session, letting a remote machine send commands and stream a terminal through it — the actual server address is pushed by Google's feature-flag system, not stored in the program. Separately, a tiny command can turn your microphone into a network stream another machine can listen to, and a sandbox socket gives local tools an execution backdoor into agent sandboxes. None of these were running on this machine, but the wiring is all in the binary.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Remote-control daemon:** `agy remote-control start --name <n> [--session]` installs `agy-remote-control.service` (systemd) / launchd plist / schtasks; `status`/`stop` manage it. Server URL is Mendel-driven (`remote-control-proxy-server-url`) — fetch via LS `GetMendelFlags` when running; do not hardcode.
- **Mesh protocol shape:** `InitiateMeshSession` → poll/send signaling messages → `ProxyCommand`/`StreamProxyCommand`. Daemon state: LS `GetRemoteControlInfo`.
- **mic-serve:** `agy mic-serve --addr 127.0.0.1:4713` (default); consumer connects over an SSH port-forward. Audio is raw TCP, no HTTP.
- **Sandbox IPC:** `/run/user/<uid>/jetski_connectd.sock` — verbs unenumerated; probing requires a running connectd with a live socket.
- **MCP extension path:** `agy mcp add` for stdio servers; `mcp_config.json` `{command, args?, env?}`; OAuth completions via LS `CompleteMcpOAuth`.
