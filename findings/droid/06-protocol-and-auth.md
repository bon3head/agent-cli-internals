# 06. Protocol and auth: LLM gateway, device-code OAuth, keyring, and the session store

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source.

## WHAT WAS FOUND

**61 distinct first-party API paths** (byte-verified census, `runs/droid/lanes/PROTOCOL.md`
§1.4 appendix; the earlier "59"/"30"/"47" counts are superseded). LLM gateway surface:
`/api/llm/a/v1/messages`, `/api/llm/o/v1/responses` (+ws), `/api/llm/g/v1/generate`,
`/api/llm/custom/usage`. Telemetry: `telemetry.factory.ai` + dev host, overridable via
`FACTORY_TELEMETRY_INGEST_BASE_URL`.

**Auth = OAuth 2.0 device-code flow (RFC 8628) via WorkOS**, with the keytar keyring as the
default credential store (`~/.factory/auth.json` backing file; `FACTORY_DISABLE_KEYRING`
opts out).

**Sessions live plaintext** on disk (`~/.factory/sessions/` + SQLite-WAL index): no
SQLCipher, no encryption (brute-force win). Mission dirs carry `progress_log.jsonl`,
`handoffs.jsonl`, `worker-transcripts.jsonl`. `git-ai` is delegation to an external binary,
not in-process logic.

**Updater is checksummed binary-only** with a SHA-256 hard gate: staged under
`~/.factory/updates/`, rename-swap install, `pending-update.json` state machine,
`droid-preserved-` prefix for rollback. An org can block updates. No script execution -
contrast with codex, whose standalone updater fetches a shell script.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

Protocol lane (endpoint census, byte-verified), brute waves (git-ai delegation, session
storage). The plaintext session store means anyone with disk access to `~/.factory/` can
read full session transcripts - including the prompts Sentry attaches to crash events.
