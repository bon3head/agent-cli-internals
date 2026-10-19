# Finding 06 — Auth: five login types; session-level, not per-method

**Version pin:** strings evidence from the **0.155.1** bun binary (auth-sessions.md §1–2;
method shapes from the **0.149.0** schema set, which pins the login-type union and the
refresh/response types). `~/.codex/auth.json` metadata confirmed live 2026-10-18
(trial row 7: `-rw-------`, 4004 bytes — values never read). `codex login status` /
`codex doctor` outputs quoted below are 0.149.0 (PATH binary). `client_id` values are
UNRECOVERABLE (self-redacting format strings — see §1).

## 1. WHAT WAS FOUND

**Five login types** (`account/login/start`, discriminated union by `type`):

1. `apiKey` — `{apiKey}`; CLI: `codex login --with-api-key` (stdin).
2. `chatgpt` — `{appBrand: "codex"|"chatgpt", codexStreamlinedLogin?, useHostedLoginSuccessPage?}` → response `{authUrl, loginId}` ("URL the client should open in a browser to initiate the OAuth flow"); CLI: `--with-access-token` (stdin, "CODEX_ACCESS_TOKEN" example env name).
3. `chatgptDeviceCode` — headless device-code flow; CLI: `codex login --device-auth`. A separate type, not a flag.
4. `chatgptAuthTokens` — inject `{accessToken (JWT), chatgptAccountId, chatgptPlanType?}` directly ("The access token must contain the same scopes that Codex-managed ChatGPT auth tokens have"). A direct token-injection vector; external clients should not use it.
   > **Correction (2026-10-19, reinforcement):** the **`[UNSTABLE] FOR OPENAI INTERNAL USE ONLY`**
   > marker text has **zero hits in 0.155.1** (two independent tools) — the marker claim is
   > UNVERIFIED/downgraded. The `chatgptAuthTokens` login type itself is VERIFIED (serde blob
   > @0xd1763d8–0xd1764a8).
5. `amazonBedrock` — `[UNSTABLE] experimental` — `{apiKey, region}`; plus `amazonBedrockAccessKeys{accessKeyId, secretAccessKey, sessionToken?, region}` (schema, 0.149.0). Bedrock is first-class: setup wizard strings, `x-amzn-mantle-client-agent` header, `AWS_BEARER_TOKEN_BEDROCK`.

**Token endpoints (binary strings, 0.155.1):**
- Refresh: `https://auth.openai.com/oauth/token` — form fields `refresh_token client_id grant_type`; observed grant `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer` + `assertion` param.
- Revoke (logout): `https://auth.openai.com/oauth/revoke` (params include `token_type_hint`, `client_id`).
- Account listing: `https://auth.openai.com/api/accounts` (shape: `access_token refresh_token client_id`).
- Inference base: `https://chatgpt.com/backend-api/...` (exact path redacted by CLI output itself; `doctor` shows websocket `wss://chatgpt.com/backend-api/...`, HTTP 405 on GET).

**`client_id` is never embedded.** Rust `format_args!` runtime placeholder (`client_id=` +
`c0 0f`) — the value is composed at runtime, not scrubbed from strings.
> **Correction (2026-10-19, reinforcement):** the "self-redacting format strings" attribution was
> wrong — the `Sensitive Data Redacted` hits are aws-sdk-ssooidc crate text, not Codex scrubbing.
> Exact `client_id` values and the device-flow authorize URL need network/dynamic tracing (UNVERIFIED).

**Token storage** (`~/.codex/auth.json`, mode 0600 — field names only, values never recorded):
top-level `auth_mode` (`ApiKey|Chatgpt|ChatgptDeviceCode|ChatgptAuthTokens|AmazonBedrock`),
`OPENAI_API_KEY` (string-or-null), `tokens{id_token, access_token, refresh_token, account_id}`,
`last_refresh` (ISO timestamp). Credential-store modes: `keyring | ephemeral`
(DBus keyring on Linux); this box overrides to file via `cli_auth_credentials_store =
"file"` in config.toml. `codex doctor` (0.149.0): `auth storage mode File`, `stored auth
mode chatgpt`, `stored API key false`, `stored ChatGPT tokens true`, `stored agent identity false`.

**Auth is session-level, not per-method.** No method schema carries an authz scope, role, or
required-token field. All `account/*` methods operate on the configured identity. Login
surfaces credentials **in request params** (`{type:"apiKey", apiKey}`, `{type:"chatgptAuthTokens", ...}`) —
a driving client must treat these as transient secrets and never log them. Refresh
lifecycle: server→client `account/chatgptAuthTokens/refresh{reason, previousAccountId?}`
tells the client to refresh tokens itself in external-auth mode;
`account/read{refreshToken?}` triggers proactive refresh in managed mode (flag ignored in
external mode). Completion arrives as `account/login/completed{loginId?, success, error?,
onboardingEntrypoint}`. There is **no OAuth device-code polling method in-schema** —
`chatgptDeviceCode` presumably completes via `account/login/completed`; browser/device
handoff details are UNKNOWN from schema alone.

**CONFIRMED vs INFERENCE:** five login types, endpoints, storage field names, session-level
auth, and the internal-only marking are CONFIRMED. Exact client_id values, device-flow
authorize URL, and token-exchange payloads are UNKNOWN (require network).

## 2. HOW IT WAS FOUND

Lane C (auth-sessions): `strings` of the 0.155.1 binary + `codex login --help` /
`codex logout` help text + local `~/.codex/` listing + the app-server schema
(`v2/LoginAccountParams.json` etc.). Trials (2026-10-18) confirmed live against 0.149.0:
`codex login status` prints `Logged in using ChatGPT`; `~/.codex/auth.json` exists at
mode 0600 (metadata only). No login/refresh/usage calls were made against live APIs;
secret VALUES were never recorded — only formats, field names, and public literals.

## 3. WHAT IT UNLOCKS

You can authenticate a headless Codex driver multiple ways — API key via stdin (no tty
needed), device-code flow for browserless machines, direct token injection for
managed environments (the internal one is off-limits, but its existence documents the
shape), or AWS Bedrock credentials. Token refresh is observable: the server either manages
it or explicitly asks your client to do it, so long-running drivers can stay alive without
user interaction.

## 4. HOW A DEVELOPER BUILDS ON IT

1. Headless login: `account/login/start{type:"chatgptDeviceCode"}` then poll
   `account/login/completed`; or pipe an API key via the CLI: `echo "$KEY" | codex login
   --with-api-key`.
2. As a driver, handle the reverse-RPC `account/chatgptAuthTokens/refresh` (Finding 02):
   refresh against `https://auth.openai.com/oauth/token` with
   `grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer` + your `assertion`, or re-run
   your own device flow. Do NOT use `chatgptAuthTokens` login type — it's internal-only.
3. Store tokens like Codex does: 0600 file, `keyring` on Linux desktops where available;
   never log `account/login/start` params (credentials ride in the request body).
4. Bedrock: `account/login/start{type:"amazonBedrock", apiKey, region}` (0.155.1; flag as
   experimental, verify against your build).
5. EU/FedRAMP: the binary carries a residency control plane
   (`x-openai-internal-codex-residency`, `chatgpt_account_is_fedramp`) — account-level, not
   per-method; verify server behavior before assuming residency routing.
