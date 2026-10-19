# 01. The binary ships its own app-server protocol spec

> **Correction (2026-10-19, reinforcement):** the counts below pin to the STALE 0.149.0 schema
> capture. Fresh emission from codex 0.155.1 (`codex app-server generate-json-schema --out`,
> deterministic across runs, byte-identical) is **102 client→server requests, 10 server→client
> requests, 82 server→client notifications, 1 client→server notification**. Delta is strictly
> additive — removed: none. New requests (7): `plugin/reconcile`, `thread/attachment/{add,list,remove}`,
> `thread/items/list`, `thread/revert`, `thread/turns/list`. New notifications (7):
> `mcpServer/event/stream/notification`, `modelProvider/authRecovery{Started,Completed}`,
> `thread/attachment/updated`, `thread/realtime/item/{started,completed,transcript/delta}`.
> Fresh schema: 37 root JSON + `v1/` (2 files) + `v2/` (273 files), at
> `~/workspace/re-suite/findings/codex/schema-0.155.1/`.

**Version pin:** schema claims verified against the app-server schema set saved at
`~/workspace/rea-codex/app-server-schema/` (291 files). Trials (2026-10-18, 8/8 CONFIRMED)
show this set is byte-identical to what `codex app-server generate-json-schema --out`
emits from the PATH binary, which is **0.149.0** at `/opt/hatch-image/bin/codex`.
So the protocol inventory below pins to **0.149.0**, not to 0.155.1.

## 1. WHAT WAS FOUND

The Codex CLI contains a built-in command that dumps its entire programmatic
interface as typed JSON Schema:

- `codex app-server generate-json-schema --out <dir>` (and `generate-ts` for TypeScript bindings)
- Emits **102 client→server requests, 10 server→client requests, 82 server→client
  notifications, 1 client→server notification** on 0.155.1 (95/10/75/1 was the stale 0.149.0
  capture: see correction note above); counts script-verified against the schema files, not hand-counted.
- The definitions come from compiled-in ts-rs Rust types (`codex-rs/app-server`), i.e. the
  spec is generated from the same structs the server actually parses, so it cannot drift from
  the implementation the way hand-written docs do.
- Two bundles are emitted: `codex_app_server_protocol.schemas.json` (title
  `CodexAppServerProtocol`, 82 defs) and `codex_app_server_protocol.v2.schemas.json`
  (title `CodexAppServerProtocolV2`, 579 defs). A `v2/` directory holds the per-method
  params/response/notification files; `v1/` holds only `InitializeParams`/`InitializeResponse`.

Evidence (0.149.0, trial row 2, `diff -rq` → zero lines, filenames identical):

```
$ codex app-server generate-json-schema --out /tmp/codex-schema-retrial
COUNT: 291 files
$ diff -rq /tmp/codex-schema-retrial ~/workspace/rea-codex/app-server-schema/
FILENAMES IDENTICAL   (content diff: zero lines)
```

The v1/v2 split, verified from the bundles: the v1 bundle's `ClientRequest` branches route
`initialize` → v1 `InitializeParams` and *every other method* → `#/definitions/v2/<Params>`,
i.e. the v1 bundle embeds the whole v2 tree. The 10 server→client requests (approval
callbacks) and the `initialized` notification exist only in the v1 bundle. Working
conclusion (CONFIRMED from bundle structure): **v2 is the current method namespace**
(`thread/*`, `turn/*`, `fs/*`, `command/exec*`, `mcpServer/*`, `config/*`, `account/*`,
`skills/*`, `plugin/*`); **v1 is the legacy layer** (handshake + approval callbacks). A
driver speaks **v2 methods over a v1 handshake**.

Key client→server methods (v2, from `~/workspace/rea-codex/app-server-schema/v2/`):

| Method | Key params |
|---|---|
| `initialize` / `initialized` | handshake (`clientInfo`, optional `capabilities`) |
| `thread/start` | `model?`, `modelProvider?`, `serviceTier?`, `cwd?`, `approvalPolicy?`, `sandbox?`, `config?`, `baseInstructions?`, `personality?` → `ThreadStartResponse{thread, ...}` (thread IDs are UUIDv7) |
| `turn/start` | `threadId`, `input: UserInput[]` (text/image/audio/skill/mention), `expectedTurnId`-less start → `TurnStartResponse{turn}` |
| `turn/steer` | `threadId`, `input`, **`expectedTurnId` (required precondition: must match the active turn)** |
| `turn/interrupt` | `threadId`, `turnId` → `{}` |
| `command/exec` (+ `/write`, `/resize`, `/terminate`) | PTY command execution in the server sandbox, client-supplied `processId`, streaming via `command/exec/outputDelta` |
| `fs/readFile`, `fs/writeFile`, `fs/watch` | host filesystem access; watch events arrive as `fs/changed` |
| `config/read`, `config/value/write`, `config/batchWrite` | runtime config access |
| `model/list`, `experimentalFeature/*` | model catalog + feature flags at runtime |

**CONFIRMED vs INFERENCE:** method inventory, parameter shapes, enums, and the v1/v2 bundle
structure are CONFIRMED (the schema is the binary's own emitted truth). Response-pairing for
non-key methods (e.g. exact `skills/list` result shape) was not mapped: treat as
UNVERIFIED. Runtime auth per method is not expressed in schema (UNVERIFIED: see Finding 06).
Wire framing (NDJSON vs length-prefixed) is not in the schema (UNVERIFIED: see Finding 02).

## 2. HOW IT WAS FOUND

Lane A (protocol-reference). Exact commands, rerun in trials (2026-10-18, live, no network):

```
codex app-server generate-json-schema --out /tmp/codex-schema-retrial   # exit 0, ~1.6 s
codex app-server generate-ts --out <dir>                                 # TypeScript bindings, field doc-comments
python3 -c "import json; json.load(open('<schema>'))"                    # shape checks
diff -rq /tmp/codex-schema-retrial ~/workspace/rea-codex/app-server-schema/  # byte-identical
```

Note: schema regen ran against the PATH binary = **0.149.0**; the REA lane report's
"0.155.1 target" header is contradicted by the trial evidence: the saved schema set is a
0.149.0 capture. Method counts (95/10/75/1) came from a script over the 291 files, not
manual enumeration.

## 3. WHAT IT UNLOCKS

Codex can be driven by *any* program (Python, Go, a web service) without screen-scraping
the terminal UI. The CLI hands you a typed, machine-readable contract for its full
capability set: start agent threads, stream turns, execute commands in a PTY, read/write the
host filesystem, flip config and experimental features, manage MCP servers, skills, and
plugins, all over a JSON-RPC socket. You no longer need to know how the binary works
internally; it tells you its own API on demand.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Launch the app-server: `codex app-server --listen stdio://` (or `unix://PATH`, `ws://IP:PORT`; see Finding 03).
2. Handshake (v1):
   - Send `{"id":1,"method":"initialize","params":{"clientInfo":{"name":"my-driver","version":"0.1.0"}}}`; wait for the response (same `id`) with `userAgent`, `codexHome`, `platformFamily`, `platformOs`.
   - Send the single client→server notification `{"method":"initialized"}` (no `id`).
3. Driver loop: `thread/start` → `turn/start` → (`turn/steer` | `turn/interrupt`) → repeat.
   - Use `"approvalPolicy":"never"` on `thread/start` to avoid having to implement the 10
     approval handlers (Finding 02) in a first prototype.
   - Thread/turn IDs are UUIDv7 strings returned in the responses.
4. Stream output from server→client notifications: `item/agentMessage/delta` (the text to
   render), `item/started`/`item/completed` (tool items), `turn/diff/updated` (file diffs),
   `turn/completed` (turn done; check `turn.status`: completed|interrupted|failed|inProgress).
5. Emit the schema locally any time the binary updates: `codex app-server generate-json-schema
   --out ./schema` and diff against the checked-in copy to detect protocol drift.
6. Suppress noise: pass `optOutNotificationMethods: ["thread/started", ...]` in
   `initialize` capabilities.

Watch out: the schema references methods that do not exist: `process/spawn`,
`thread/turns/list`, `thread/items/list` are named in doc comments but absent from
`ClientRequest` (verified, 0.149.0). No client request starts a realtime session either
(all `thread/realtime/*` notifications are EXPERIMENTAL with no request method). Do not
generate code that assumes these exist.
