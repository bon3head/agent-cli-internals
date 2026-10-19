# Finding 03 — Transports: stdio, unix socket, websocket

**Version pin:** from `codex app-server --help`, verified live against the PATH binary
(**0.149.0**, trial row 5, 2026-10-18). Remote bearer-token wiring via
`--remote-auth-token-env` verified in `--help` of both `app-server` and `agents` on
0.149.0. The websocket auth handshake itself is UNVERIFIED (no live remote connection made).

## 1. WHAT WAS FOUND

`codex app-server --listen <URL>` accepts (byte-exact help text, 0.149.0):

- `stdio://` — default; the client and server talk over the server process's stdin/stdout.
- `unix://` / `unix://PATH` — listen on a Unix-domain socket (PATH form takes an explicit path).
- `ws://IP:PORT` — listen on a TCP websocket; a remote driver can attach over the network.
- `off` — do not start the app-server.

Remote authentication: `--remote-auth-token-env <ENV_VAR>` names an environment variable
whose value is the bearer token used for the remote (ws) connection. The help text
deliberately redacts the word "token" itself — the flag description says something like
"bearer ... " with the sensitive word scrubbed, which is itself evidence of the
redaction discipline in this CLI.

Related surface (CONFIRMED, same help output, 0.149.0):
- `codex agents` — "Browse all agent sessions on the shared local app-server daemon";
  takes `--remote <ws://|wss://|unix://|unix://PATH>` plus the same
  `--remote-auth-token-env <ENV_VAR>` bearer wiring.
- `codex remote-control [start|stop|pair]` — `[experimental]` daemon with remote control;
  `pair` prints a short-lived manual pairing code. Daemon state dir `~/.codex/app-server-daemon/`
  (on this box: settings.json missing, "app-server not running (ephemeral mode)").

**CONFIRMED vs INFERENCE:** the transport URL shapes and the env-var bearer mechanism are
CONFIRMED from `--help`. The actual ws auth handshake (header? query param? subprotocol?)
is UNVERIFIED — no remote connection was established. `wss://` (TLS) appears as an
`agents --remote` value but `app-server --listen` help shows only `ws://`; whether the
server side terminates TLS is UNKNOWN.

## 2. HOW IT WAS FOUND

Lane A + lane C (auth-sessions) help scraping, rerun in trials:

```
codex --help            # exit 0; top-level lists agents, exec, review, login, logout, mcp,
                        # plugin, mcp-server, app-server, remote-control, completion, update,
                        # doctor, sandbox, debug, apply, resume, queue, archive, delete
codex app-server --help # lists daemon, proxy, generate-ts, generate-json-schema subcommands;
                        # --listen URL values: stdio:// (default), unix://, unix://PATH,
                        # ws://IP:PORT, off
codex agents --help     # --remote <ws://|wss://|unix://|unix://PATH> --remote-auth-token-env
```

Zero network calls; read-only `--help` invocations plus the `~/.codex/app-server-daemon/`
directory listing.

## 3. WHAT IT UNLOCKS

You are not limited to spawning a child process on the same machine. The same app-server
can be driven over a local socket (no stdio interleaving problems in containerized setups)
or over TCP from another host entirely — so a fleet coordinator, a web dashboard, or an
agent running on different hardware can all hold live Codex sessions. The env-var bearer
token keeps the credential out of argv and process listings.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Local, simplest: `codex app-server --listen stdio://` and drive JSON-RPC over
   stdin/stdout (frame convention NDJSON — verify at runtime; see Finding 02).
2. Local socket (cleaner for supervisors): `codex app-server --listen unix:///tmp/codex.sock`.
3. Remote: `codex app-server --listen ws://0.0.0.0:8765` with the bearer token in an env var
   named by `--remote-auth-token-env CODEX_REMOTE_BEARER`; the client sets the same env var
   before connecting (`codex agents --remote ws://host:8765 --remote-auth-token-env
   CODEX_REMOTE_BEARER`). Confirm the auth wire format (header vs subprotocol) against a live
   server before deploying — it is the one unverified piece.
4. Ephemeral vs daemon: by default the app-server runs in ephemeral mode alongside the
   client; `codex remote-control start` runs the shared daemon for `codex agents` browsing.
5. On top of any transport, the protocol from Finding 01 is identical: initialize →
   initialized → thread/start → turn/start → steer/interrupt.
