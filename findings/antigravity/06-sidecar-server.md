# 06. Sidecar web server: token-authenticated local HTTP agent handle

> **Correction (2026-10-19, reinforcement):** prior-pass `@`-offsets in this doc did not reproduce
> (reverify + `grep -boa` agree with each other, not with prior). Corrected offsets below, all in
> the embedded Node bundle (`.noptrdata`).

**Trial status:** CONFIRMED at suite level (17/17 on the same binary). Not separately re-trialed; stands on lane A1 evidence. Live only while a sidecar run is active: none was running at trial time.

---

## 1. WHAT WAS FOUND

Each scheduled sidecar runs an **embedded Node HTTP server on `127.0.0.1:<ANTIGRAVITY_SIDECAR_WEB_PORT>`**. Byte evidence from the embedded Node bundle (CONFIRMED):

- `const BIND_HOST = '127.0.0.1';` @187272392 with an in-code comment warning that binding a routable interface would publish the API unprotected.
- Auth: header `x-sidecar-token` or `?token=`, value = `ANTIGRAVITY_SIDECAR_UI_TOKEN`; `#validateToken` @187279440 (0xb29a850) requires it on all non-GET requests. `/preload.js` is unauthenticated. If no token is configured, auth is skipped entirely.
- Routes (embedded class; corrected offsets):
  - `POST /_sidecar/send-message` @187275674: `{conversationId, message, title?, projectId?}`
  - `POST /_sidecar/new-conversation` @187275865: `{message, model?, projectId?}`
  - `POST /_sidecar/get-conversation-metadata` @187276029: `{conversationId}`
  - plus extensible `/_sidecar/*` per-sidecar routes.
- Backing ops shell out to the LS over the Connect endpoint: `ANTIGRAVITY_LS_ADDRESS` + `ANTIGRAVITY_CSRF_TOKEN` are injected into the sidecar process env.

Sidecar config lives at `~/.gemini/config/sidecars/<sidecar-id>/sidecar.json` (IDE/2.0-side; not present on this CLI-only box). LS spawns the sidecar manager via `language_server.(*Server).maybeStartSidecarManager` @40918120 (0x2705c9a; prior @18857783 did not reproduce). On this machine the LS itself was not running at trial time.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

INFERENCE/limits: only live while a sidecar run is active; port is dynamic per run.

---

## 2. HOW IT WAS FOUND

Lane A1 (control planes). The eureka (~22:10): the sidecar web-server blueprint was found in the embedded Node bundle; bind host, `#validateToken` logic, and `/_sidecar/*` routes all as adjacent rodata. Surfaced by `pocs/a1_enumerate_surfaces.py` and verified by offset-anchored greps.

---

## 3. WHAT IT UNLOCKS

When the agent runs a sidecar (a scheduled background session), it also starts a tiny private web server on your machine with its own token. That is a hidden remote control with a much simpler handle than the full language server: send it an HTTP POST and you can inject a message into a running conversation or start a new one. It only binds to localhost, by explicit design: the code warns against exposing it to a network. For automation, it is the easiest programmatic agent handle after the language server itself.

---

## 4. HOW A DEVELOPER BUILDS ON IT

```bash
# Port + token come from the sidecar's process environment (dynamic per run)
curl -sS -X POST "http://127.0.0.1:${ANTIGRAVITY_SIDECAR_WEB_PORT}/_sidecar/new-conversation" \
  -H "Content-Type: application/json" \
  -H "x-sidecar-token: ${ANTIGRAVITY_SIDECAR_UI_TOKEN}" \
  -d '{"message":"summarize the workspace","projectId":"default-cli-project"}'

curl -sS -X POST "http://127.0.0.1:${ANTIGRAVITY_SIDECAR_WEB_PORT}/_sidecar/send-message" \
  -H "Content-Type: application/json" \
  -H "x-sidecar-token: ${ANTIGRAVITY_SIDECAR_UI_TOKEN}" \
  -d '{"conversationId":"<id>","message":"continue"}'

curl -sS -X POST "http://127.0.0.1:${ANTIGRAVITY_SIDECAR_WEB_PORT}/_sidecar/get-conversation-metadata" \
  -H "Content-Type: application/json" \
  -H "x-sidecar-token: ${ANTIGRAVITY_SIDECAR_UI_TOKEN}" \
  -d '{"conversationId":"<id>"}'
```

Notes: token also accepted as `?token=`. Only live while the sidecar run is active. Keep the bind on loopback: the code explicitly warns a routable bind publishes the API unprotected. Discovery of a live sidecar: scan `ANTIGRAVITY_SIDECAR_WEB_PORT` in sidecar process env, or `GetSidecars`/`ListSidecarLogFiles` on the LS.
