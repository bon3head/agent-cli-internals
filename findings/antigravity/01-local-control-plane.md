# 01 — Local control plane: the language server is a fully drivable agent socket

**Trial status:** CONFIRMED. `a1_enumerate_surfaces.py` re-run exit 0, 341 methods recounted; `a1_probe_health.py` re-run exit 0 (connection refused = no LS running, expected). Port 5387 tested CLOSED at trial time. Full 17/17 trial suite passed on the same binary. **Caveat:** live method probing needs a running LS plus a valid CSRF token — not yet done.

---

## 1. WHAT WAS FOUND

The Antigravity language server exposes `exa.language_server_pb.LanguageServerService` — **341 real RPC methods** — over ConnectRPC (connect-go) as cleartext HTTP/1.1 + h2c on loopback at `localhost:5387` (`ANTIGRAVITY_LS_ADDRESS`). The binary embeds the exact recipe for driving it (strings @421532, byte-exact):

```
: "${ANTIGRAVITY_LS_ADDRESS:=localhost:5387}"
curl -sS "http://${ANTIGRAVITY_LS_ADDRESS}/healthz"
curl -sS -X POST "http://${ANTIGRAVITY_LS_ADDRESS}/exa.language_server_pb.LanguageServerService/$1" \
  -H "Content-Type: application/json" -H "x-codeium-csrf-token: <redacted>" -d "$2"
```

CONFIRMED byte evidence:
- Protocol symbols: `connect.NewLanguageServerServiceHandler` (strings @17240626), `h2c.NewHandler` (@17066873) — gRPC / gRPC-Web / Connect-JSON all hit the same handlers.
- Method inventory: `a1_inventory.txt` (603 lines) lists all 341 with string offsets, e.g. `AcceptTermsOfService @24051494`, `CompleteMcpOAuth @24001393`.
- Method clusters: Cascade agent control (`StartCascade`, `SendUserCascadeMessage`, `ForkConversation`, `RevertToCascadeStep`, `SendStepsToBackground`), trajectory memory (`GetAllCascadeTrajectories`, `ConvertTrajectoryToMarkdown`, `ReplayGroundTruthTrajectory`), skills/plugins/MCP (`GetAllSkills`, `InstallCascadePlugin`, `ToggleMcpServer`, `CompleteMcpOAuth`, `LaunchMcpApp`), terminals (`CreateTerminal`, `StreamTerminalOutput`, `SendTerminalInput`), VCS (Git/Jj/Cog/Fig/Repo families), browser automation (`CaptureScreenshot`, `SmartOpenBrowser`, `AddToBrowserWhitelist`), audio (`SendAudioChunk`, `StreamAudioTranscription`), sidecars (`GetSidecars`, `ManageSidecar`), auth/config (`HasAuthToken`, `SetUserSettings`, `GetMendelFlags`), server mgmt (`DumpPprof`, `DumpFlightRecorder`, `SimulateSegFault`, `Restart`, `Exit`).
- Auth: mutating methods require header `x-codeium-csrf-token` (strings @421544: `-H \"x-codeium-csrf-token: ${ANTIGRAVITY_CSRF_TOKEN}\"`); token is exported into every sidecar/shell env. `/healthz` is unauthenticated in the literal curl.
- Companion surfaces from the same lane: `exa.api_server_pb.ApiServerService` (90 backend methods, telemetry/config), BOQ `devtools_jetski_boq_api_proto.ApiService` (18 remote-control signaling methods), sidecar HTTP, `agy mic-serve` (loopback audio, 127.0.0.1:4713), `jetski_connectd.sock` sandbox IPC, MCP child processes over stdio.

Target pinned: `agy` v1.3.1, `/home/hatch/.local/bin/agy`, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

INFERENCE (not verified): whether `/healthz` truly needs no token (literal shows bare curl only); how the CLI discovers vs spawns an LS.

---

## 2. HOW IT WAS FOUND

Lane A1 (control planes), strings/schema/behavioral tier, read-only. Steps:
1. Extracted string table: `strings` → `deep-dive/agy.strings` (1,924,440 lines, 47MB).
2. PoC `pocs/a1_enumerate_surfaces.py` — deconcat heuristics over the string table to separate real method names from descriptor-byte concat artifacts. Ran: `python3 pocs/a1_enumerate_surfaces.py /home/hatch/.local/bin/agy` → 603-line `pocs/a1_inventory.txt`.
3. The embedded curl recipe was found verbatim at strings line 421532 — the binary documents its own control plane.
4. PoC `pocs/a1_probe_health.py` — single-shot `GET /healthz` with 2s timeout: `python3 pocs/a1_probe_health.py` → `NOT RUNNING: URLError: <urlopen error [Errno 111] Connection refused>` (exit 0 by design).
5. Trial re-run (2026-10-18): same outputs; `timeout 2 bash -c '</dev/tcp/127.0.0.1/5387'` → `Connection refused` — port closed at trial time, consistent with the probe.

---

## 3. WHAT IT UNLOCKS

The CLI ships with a hidden remote control: a local agent server that listens on your own machine and accepts plain-JSON commands for everything the IDE can do — start an agent task, list past conversations, open terminals, push git commits, manage plugins. The token that authorizes it is sitting in your shell environment, so any local tool can drive the whole agent stack with ordinary curl. No SDK, no plugin framework, no reverse-engineering of a private protocol: the binary literally contains the curl recipe.

---

## 4. HOW A DEVELOPER BUILDS ON IT

**Drive the LS with curl (no SDK):**

```bash
# Address + CSRF token come from the agent/sidecar shell environment
: "${ANTIGRAVITY_LS_ADDRESS:=localhost:5387}"          # default per embedded doc
curl -sS "http://${ANTIGRAVITY_LS_ADDRESS}/healthz"   # liveness (no token in literal)
curl -sS -X POST "http://${ANTIGRAVITY_LS_ADDRESS}/exa.language_server_pb.LanguageServerService/GetStatus" \
  -H "Content-Type: application/json" \
  -H "x-codeium-csrf-token: ${ANTIGRAVITY_CSRF_TOKEN}" \
  -d '{}'
```

Method URL form: `/exa.language_server_pb.LanguageServerService/<MethodName>`; POST JSON body; any of gRPC / gRPC-Web / Connect-JSON are accepted by the same handlers.

Useful first calls: `GetStatus`, `GetUserSettings`, `GetAllSkills`, `GetAllCascadeTrajectories`, `ListTerminals`, `CreateTerminal`, `GetMendelFlags`.

**Limits a developer must know:** per-method JSON request schemas are unrecoverable at this tier (proto descriptors stripped from the binary) — schemas must be learned by live probing against a running LS with a valid token. `/healthz` auth requirement unverified. LS process lifecycle (who spawns it) unverified.

Related env vars: `ANTIGRAVITY_LS_ADDRESS`, `ANTIGRAVITY_CSRF_TOKEN`, `ANTIGRAVITY_PROJECT_ID`, `ANTIGRAVITY_CONVERSATION_ID`, `ANTIGRAVITY_TRAJECTORY_ID`.
