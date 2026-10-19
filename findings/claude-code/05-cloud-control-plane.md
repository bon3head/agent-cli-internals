# 05. Cloud-session control plane mapped (C2)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C2 (cloud/gateway) · **Trial status:** CONFIRMED live (`pocs/cloud_mapper.py` re-run:
exit 0, 291 distinct values across 8 tables: exact match of the REPORT claim; `claude --help` shows
`--cloud`/`gateway`/`ultrareview` live)
**Confidence:** CONFIRMED (byte-level). The `--client-data-url` "exact URL" validation semantics and the
wake-on-comment server-side mechanism are INFERENCE from adjacent copy; wire protocol details
(attach frame ordering, create-body field names) UNVERIFIED (no network allowed).

---

## 1. WHAT WAS FOUND

The complete cloud-session lifecycle is embedded in the binary:

- `--cloud [description|session_id|url]`: "Create a cloud session with the given description, or
  attach to an existing one by session ID or claude.ai/code URL" (`claude --help`).
- Session IDs match `^(?:session|cse)_[A-Za-z0-9_-]+$` (byte-confirmed regex).
- A per-flag treatment matrix (the `gs` object) governs **every flag** at create/attach:
  - **refused** (hard error: `"Error: a cloud session cannot honor these options yet, so they are
    refused rather than silently dropped; start it without ..."`): `--dangerously-skip-permissions`,
    `--bare` ("a cloud session signs in with this machine's claude.ai login, which --bare turns
    off"), `--restricted`, `--safe-mode`, `--json-schema`, `--watch-artifact`, `--plugin-dir/url`,
    `--await-claim`, SDK MCP servers; on attach: `--tools`, `--disallowed-tools`, `--max-turns`,
    `--max-budget-usd`.
  - **silently dropped** (`ignore/lost`): `--add-dir`, `--betas`, `--chrome`, `--file`, `--init`,
    `--maintenance`, `--system-prompt-snapshot`, `--session-mirror`.
  - **client-only**: `--debug`, `--verbose`, `--output-format`, `--input-format`,
    `--setting-sources`.
  - **forwarded at create**: `--model`, `--name`, `--effort`, `--fallback-model`,
    `--system-prompt*`, `--thinking*`, `--permission-mode` (non-bypass), `--allowed-tools`.
- Attach is a streaming frame protocol (`headlessCloudClient`) over `/v1/code/agent-proxy`
  (or per-session `/v1/code/sessions/{id}/agent-proxy`). Frame/event names verbatim:
  `cloud_session`, `cloud_session_delta`, `worker_frame`, `workerEpoch`, `hook_callback`,
  `hook_forwarding_disabled`, `hook_forwarding_not_ready`, `initialMessage`,
  `cloudSessionKeysDropped`. End states: `session_start_failed`, `session_archived`,
  `session_not_found`, `orchestrator_error`.
- The cloud container's denial set is byte-verbatim: "Nothing was read or written" for the
  credential file, keychain/Credential Manager, SSH keys, cloud-provider credentials;
  settings files cannot be changed from shell; host tool offering is consent-gated; cloud
  sessions sign in with the machine's claude.ai login (unavailable on Bedrock/Vertex/Foundry).
- `--environment <id>` (alias `--pool`) runs cloud sessions on self-hosted runners (`ccpool_…`):
  full admin provisioning flow embedded (Admin settings → Cloud environments → environment key
  → `./runner-setup/ENVIRONMENT_SECRET`, chmod 600); runner diagnostics:
  `self_hosted_runner_get_pool`, `self_hosted_runner_list_runners`,
  `self_hosted_runner_list_sessions`, `self_hosted_runner_read_health`; health probe
  `GET http://127.0.0.1:{health_port}/healthz`.
- `--teleport [session]` pulls a cloud session into a local terminal with full history:
  `handleTeleportPrerequisites` → `validateGitState` → `stashToCleanState` →
  `teleportFromSessionsAPI` → `pollRemoteSessionEvents` → `teleportResumeCodeSession`.
- Wake-on-comment: server-pushed comment events + client-side consent record ("comment-monitoring
  consent record(s) handed to the next wake of this session"). **KILL:** the term
  "wake-on-comment" is descriptive: no local `wake*comment` identifier exists.
- `claude ultrareview [options] [target]`: "Run a cloud-hosted multi-agent code review of the
  current branch"; preflight `GET /v1/ultrareview/preflight`, quota `GET /v1/ultraveview/quota`
  (`auth:"teleport-org"`), `--post` posts findings via `/v1/code/github/post-review-comment`.
  **KILLS:** ultrareview uploads a partial clone (byte evidence: the review runs "over the
  branch diff": "may include staged and unstaged changes you haven't committed yet, but not
  untracked files"); ultrareview does credential-file checks (no strings; the cloud session's
  own denial set applies).

## 2. HOW IT WAS FOUND

- Lane C2: `re.findall(rb'[ -~]{6,}')` on the 244 MB binary → 521,976 runs in 13 s; windowed
  context mining (±350 chars via `re.finditer`) after `grep -o` truncation kept destroying
  minified-JS context (`scratchpad-c2.md`).
- The `gs` treatment matrix decoded from the object literal: every cloud flag-compatibility
  row traced to its treatment code (`client`/`create`/`ignore-lost`/`ignore-preference`/
  `ignore-kept`/`moot`/`refuse`).
- Session-id regex, runner endpoints, teleport pipeline, and denial strings all extracted as
  byte-verbatim quotes; the endpoint inventory lands in `pocs/cloud-map/cloud-map.md`.
- PoC: `pocs/cloud_mapper.py` → 8 tables (endpoints: 19, api_paths: 78, flags: 18,
  env_vars: 18, id_prefixes: 3, gateway_keys: 6, hosts: 145, session_id_formats: 4) =
  291 distinct values; trial re-run produced the identical count.
- Kills verified by absence searches in the binary strings.

## 3. WHAT IT UNLOCKS

In plain terms: you can now see the whole cloud session lifecycle (start, attach, migrate,
and pull back home) as documented, scriptable machinery. You know exactly which of your
local flags survive the trip (model, effort, system prompt) and which are silently dropped
or hard-refused, which is the difference between a cloud session that behaves like your local
one and one that mysteriously ignores half your configuration.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Flag compatibility check before launching:** any automation that spawns
  `claude --cloud` should filter flags through the treatment matrix: forward `Se` flags
  (model/effort/system-prompt), warn on `ignore/lost` flags (`--add-dir`, `--plugin-dir`,
  `--watch-artifact`), and fail fast on `refuse` flags (`--bare`,
  `--dangerously-skip-permissions`) instead of hitting the hard error.
  ([pocs/cloud-map/cloud-map.md](sandbox://workspace/rea-claude/deep-dive/pocs/cloud-map/cloud-map.md))
- **Session lifecycle tooling:** `claude --cloud <session_id>` (attach),
  `claude --teleport <session_id>` (pull local with full history), session IDs match
  `^(?:session|cse)_[A-Za-z0-9_-]+$`: validate IDs client-side before invoking.
- **Self-hosted runner fleet:** the ccpool provisioning flow + runner API
  (`/v1/code/runners/self-hosted/*`, health probe `GET 127.0.0.1:{port}/healthz`) is fully
  specified: stand up pool environments, monitor them with `self_hosted_runner_read_health`
  / `read_metrics` / `tail_log`.
- **Attach protocol:** streaming frames (`cloud_session`, `worker_frame`, `workerEpoch`)
  over `/v1/code/agent-proxy` with local-hook callback registrations (`hook_callback`):
  the seam for a custom attach client or session mirroring dashboard.
- **Code-review automation:** `claude ultrareview <PR#>` runs multi-agent review over the
  branch diff; `--json` + `--no-post` gives findings without touching the PR.
