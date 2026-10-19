# 10. `codex cloud` is experimental-tagged but fully present

**Version pin:** subcommand inventory from `codex cloud --help`, verified live against the
PATH binary (**0.149.0**, trial row 5, 2026-10-18). Implementation strings (`cloud-tasks`
crate) from the **0.155.1** binary. API paths and end-to-end task execution are
UNVERIFIED (no network; endpoints are constructed at runtime, not string literals).

## 1. WHAT WAS FOUND

`codex cloud` carries the `[EXPERIMENTAL]` tag in help, but the tag is a **support-policy
marker, not a stub marker**. Five working subcommands ship in the binary (0.149.0, help text
byte-verbatim):

- `cloud exec --env <ENV_ID> [--attempts N (best-of-N, default 1)] [--branch <BRANCH> (defaults to current)] [QUERY]`: "Submit a new Codex Cloud task without launching the TUI"
- `cloud status <TASK_ID>`: task status
- `cloud list`: list tasks
- `cloud apply <TASK_ID> [--attempt <N>]`: "Apply the diff for a Codex Cloud task locally"
- `cloud diff <TASK_ID>`: "Show the unified diff"

Help one-liner: "Browse tasks from Codex Cloud and apply changes locally."

**Implementation is real (0.155.1 strings, CONFIRMED):** Rust crate `cloud-tasks`
(`cloud-tasks/src/lib.rs, app.rs, ui.rs, util.rs, env_detect.rs`) +
`cloud-config/src/service.rs`; a TUI list UI (`codex_cloud_tasks_tui`) with environment
detection (`"single environment available; selecting it"`, `env_detect.rs:379`). Env
override: `CODEX_CLOUD_TASKS_BASE_URL`. Backend base is `https://chatgpt.com/backend-api/`:
the only task-adjacent paths found as literals are `codex`,
`code_challenge_methods_supported`, `plugins/export/curated`; **exact task API paths are
constructed at runtime and were not recovered** (UNVERIFIED).

**The local half:** `codex apply` (alias `a`): "Apply the latest diff produced by Codex
agent as a `git apply` to your local working tree". The cloud flow is: remote agent runs
the task → `cloud diff <TASK_ID>` to inspect → `cloud apply <TASK_ID>` (or `codex apply`)
to land the unified diff locally with `git apply`.

**CONFIRMED vs INFERENCE:** the five subcommands, their flags, the crate/module names,
`CODEX_CLOUD_TASKS_BASE_URL`, and the `git apply` local half are CONFIRMED. API paths,
env-list semantics, and whether tasks run end-to-end without the TUI are UNVERIFIED (no
network). The `[EXPERIMENTAL]` tag means the surface may change without notice: treat
as a policy fact, not a quality judgment.

## 2. HOW IT WAS FOUND

Lane C (auth-sessions §4): `codex cloud --help` and `codex apply --help` on the PATH binary
(0.149.0), re-verified live in trials 2026-10-18; `strings` of the 0.155.1 binary for the
`cloud-tasks` crate paths and `CODEX_CLOUD_TASKS_BASE_URL`; grep of `backend-api/...`
string literals (only `codex`, `code_challenge_methods_supported`,
`plugins/export/curated` surfaced: task paths absent).

## 3. WHAT IT UNLOCKS

Codex Cloud turns the CLI into a thin client for remote agents: submit a task with
`cloud exec --env <ENV_ID>`, watch `cloud status`, pull the unified diff with `cloud
diff`, and apply it locally: all without opening the TUI. For automation, that means
CI-like agent runs whose results land in your working tree as an ordinary patch you can
review before applying.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Authenticate (Finding 06): cloud talks to `https://chatgpt.com/backend-api/` under
   your Codex identity.
2. Submit: `codex cloud exec --env <ENV_ID> --attempts 3 --branch main "refactor the
   auth module"` (best-of-N attempts; branch defaults to current).
3. Poll: `codex cloud status <TASK_ID>`; list: `codex cloud list`.
4. Inspect before applying: `codex cloud diff <TASK_ID>` (unified diff), then
   `codex cloud apply <TASK_ID> [--attempt N]` to `git apply` it into your working tree.
5. Repoint the backend: `CODEX_CLOUD_TASKS_BASE_URL` env (e.g. staging).
6. Caveats: `[EXPERIMENTAL]`; pin your build and diff `codex cloud --help` output across
   upgrades; exact API paths are runtime-constructed, so don't hardcode URL paths from
   string dumps.
