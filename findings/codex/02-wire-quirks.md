# 02. Wire-envelope quirks that break naive JSON-RPC clients

**Version pin:** all claims verified against the schema set pinned to **0.149.0**
(byte-identical regen confirmed in trials, 2026-10-18). Wire behavior (actual frames on a
live socket) is UNVERIFIED: no live app-server session was driven; "NDJSON" below is
convention inference, not observed fact.

## 1. WHAT WAS FOUND

Three protocol quirks that would silently break a standard JSON-RPC client library:

**a) There is no `"jsonrpc": "2.0"` version field.** `JSONRPCRequest` requires only
`["id","method"]`; optional `params` and an optional W3C `trace` (`traceparent`/`tracestate`).
Byte-exact schema quote (0.149.0, `~/workspace/rea-codex/app-server-schema/JSONRPCRequest.json`):

```json
{
  "description": "A request that expects a response.",
  "properties": {
    "id":   { "$ref": "#/definitions/RequestId" },
    "method": { "type": "string" },
    "params": true,
    "trace": { "...": "Optional W3C Trace Context for distributed tracing." }
  },
  "required": ["id", "method"],
  "title": "JSONRPCRequest",
  "type": "object"
}
```

No `jsonrpc` property exists anywhere in the schema, and a client that *mandates* the
version field (most off-the-shelf JSON-RPC libraries reject requests without it) will fail.
Client→server request branches additionally require `params` (`["id","method","params"]`).

**b) The 10 server→client requests are a mandatory reverse-RPC channel.** The server sends
requests *to the client* with an `id`, and the client MUST answer with the matching
response type or the agent stalls mid-turn. This is not optional event handling:

| Method | What the agent is waiting for |
|---|---|
| `item/commandExecution/requestApproval` | approve/deny running a command |
| `item/fileChange/requestApproval` | approve/deny writing files |
| `item/permissions/requestApproval` | approve/deny a permission-profile grant |
| `item/tool/requestUserInput` | a mid-turn question to the user (blocking-capable, EXPERIMENTAL) |
| `mcpServer/elicitation/request` | form-fill or URL elicitation from an MCP server |
| `item/tool/call` | server delegates a dynamic tool call to the client for execution |
| `account/chatgptAuthTokens/refresh` | refresh ChatGPT tokens (external-auth clients) |
| `attestation/generate` | an attestation blob |
| `applyPatchApproval` / `execCommandApproval` | legacy (v1-style `conversationId`/`callId` fields) approvals |

A driver is not fire-and-forget. Any restrictive `approvalPolicy` (anything other than
`"never"`) obligates the client to implement these handlers.

**c) Multi-client concurrency is designed in, not bolted on.**
- `turn/steer` carries a required `expectedTurnId` precondition: it fails unless the value
  matches the currently active turn.
- Approval resolutions correlate via `serverRequest/resolved{threadId, requestId}`.
- `initialize` capabilities include `optOutNotificationMethods: string[]` to suppress
  specific notification methods.

**CONFIRMED vs INFERENCE:** (a)–(c) are CONFIRMED from the emitted schema. Whether real
live frames are newline-delimited JSON (NDJSON) is INFERENCE from stdio JSON-RPC convention:
the schema is silent on framing. Actual approval-callback timing, and whether the server
actually rejects connections with multiple racing clients, is UNVERIFIED (no live session).

## 2. HOW IT WAS FOUND

Lane A. Commands (rerun in trials, 2026-10-18, live):

```
codex app-server generate-json-schema --out /tmp/codex-schema-retrial
python3 -c "import json; d=json.load(open('/tmp/codex-schema-retrial/JSONRPCRequest.json')); \
  print(d['required']); print(list(d['properties']))"
# → ['id', 'method']
# → ['id', 'method', 'params', 'trace']
```

Lane A then enumerated the `ServerRequest` (10) and `ClientNotification` (1, `initialized`)
branches in the v1 bundle and correlated each reverse request with its `*Response` file in
`v2/`.

## 3. WHAT IT UNLOCKS

A correct Codex driver can be written once and won't mysteriously stall. Knowing the missing
`jsonrpc` field up front saves the "why does the server ignore my perfectly valid requests"
debugging loop. Knowing approvals are reverse-RPC tells you the driver needs a request
handler, not just an event listener, and that `approvalPolicy: "never"` is the escape
hatch for prototypes. The `expectedTurnId` + `serverRequest/resolved` correlation design
means dashboards, CLIs, and bots can safely share one Codex thread without stepping on
each other.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Use a minimal hand-rolled JSON-RPC frame writer; do not use a strict JSON-RPC 2.0 library,
   or configure it to omit/ignore the `jsonrpc` version field on both send and receive.
2. IDs: `RequestId` = `string | int64`; pick one and be consistent.
3. Frame assumption for stdio: newline-delimited JSON. Verify at runtime against a live
   `codex app-server --listen stdio://` before shipping.
4. Implement the reverse-RPC dispatcher: on receiving any server→client request, reply with
   `{"id": <same>, "result": <matching response shape>}` from the schema files; correlate
   the eventual `serverRequest/resolved{threadId, requestId}` notification to close out the
   pending approval in your UI.
5. If you don't want to build approval UI yet: set `approvalPolicy: "never"` on
   `thread/start`; the server will never emit approval requests.
6. For concurrent steering: read the active turn id from `turn/started` and always send it as
   `expectedTurnId`; retry steer on precondition failure after re-reading state.
7. Reduce traffic: pass `optOutNotificationMethods` with the notification names you ignore
   (e.g. `thread/started`, `item/reasoning/summaryPartAdded`).
