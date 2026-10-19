# 09 — Auth plane: endpoints, client IDs, storage, providers (C4)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C4 (auth) · **Trial status:** CONFIRMED live
(`pocs/auth-surface-audit.py` re-run → exit 0: `~/.claude/.credentials.json: exists=yes mode=0o600`,
`top-level keys: ['claudeAiOauth']`, `Linux: no OS keychain used; file fallback
~/.claude/.credentials.json is authoritative`; `stat` → `600 519` — **metadata only, no values**)
**Confidence:** CONFIRMED (byte-level). Refresh-grant endpoint selection, macOS keychain OAuth
service/account names, and the `/login` managed-key backing store are UNRESOLVED (killed/unknown).

---

## 1. WHAT WAS FOUND

The complete credential-source taxonomy (verbatim union from a zod describe string):

- `'ANTHROPIC_API_KEY'` (env), `'apiKeyHelper'` (configured helper command), `'/login managed
  key'` (API key created and stored by `/login` with a Console account), `'none'` — extended at
  runtime with `'ANTHROPIC_AUTH_TOKEN'`, `'CLAUDE_CODE_OAUTH_TOKEN'`,
  `'CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR'`, `'CLAUDE_CODE_GATEWAY_TOKEN_FILE_DESCRIPTOR'`,
  `'from the OAuth token file'`, `'from the saved claude.ai login'`,
  `'from ANTHROPIC_CUSTOM_HEADERS'`, `'from CLAUDE_CODE_CONTAINER_ID'`,
  `'from CLAUDE_CODE_REMOTE_SESSION_ID'`, `'from CLAUDE_CODE_ENTRYPOINT'`.
  Legacy members `'user'|'project'|'org'|'temporary'|'oauth'` are never emitted.

OAuth endpoints (byte-exact config block): `https://claude.com/cai/oauth/authorize`
(subscription), `https://platform.claude.com/oauth/authorize` (console),
`https://platform.claude.com/v1/oauth/token` (token), `create_api_key` + `roles` at
`api.anthropic.com/api/oauth/claude_cli/*`. Flow: browser + RFC 8628 device-code flow
(`urn:ietf:params:oauth:grant-type:device_code`, `/device` HTML form), PKCE authorization-code
exchange, 30s keychain re-check loop on refresh (`"auth: no token found, will re-check
keychain every 30s"`).

Storage: Linux `~/.claude/.credentials.json` mode 0600, schema
`claudeAiOauth -> { accessToken, refreshToken, expiresAt, refreshTokenExpiresAt, scopes,
subscriptionType, rateLimitTier }` (shapes only — 108-char strings, epoch-ms ints, **no values
read or recorded**); `~/.claude.json` mode 0600 holds account/org metadata only. macOS via
the `security` CLI (`find-generic-password` / `add-generic-password -U`); Windows via
Credential Manager (`CredRead`/`CredWrite`).

`claude setup-token`: "Set up a long-lived authentication token (requires Claude
subscription)" — 1-year token, shown once, consumed via `CLAUDE_CODE_OAUTH_TOKEN` (never
written to disk), defaults to `user:inference` scope only.

`apiKeyHelper` protocol (verbatim): "The script must print only the key to stdout.";
"apiKeyHelper output rejected: not a printable-ASCII token"; TTL via
`CLAUDE_CODE_API_KEY_HELPER_TTL_MS`; security gate: "apiKeyHelper requires workspace trust"
(never runs before trust is confirmed).

`--bare` semantics (verbatim): "Anthropic auth is strictly ANTHROPIC_API_KEY or apiKeyHelper
via --settings (OAuth and keychain are never read)." Bare mode also disables hooks, LSP,
plugin sync, keychain reads, CLAUDE.md auto-discovery.

Provider paths (byte-exact): Bedrock (`https://bedrock-runtime.{region}.amazonaws.com`,
`https://bedrock.{region}.amazonaws.com`, mantle `https://bedrock-mantle.{region}.api.aws/anthropic`),
Vertex (`https://claude.googleapis.com`), Foundry (Azure `DefaultAzureCredential` full
chain, scope `https://cognitiveservices.azure.com/.default`), Anthropic-AWS
(`https://aws-external-anthropic.{region}.api.aws`). Selection env vars:
`CLAUDE_CODE_USE_BEDROCK/VERTEX/FOUNDRY/ANTHROPIC_AWS/ANTHROPIC_GOOGLE_CLOUD/MANTLE` (+
`SKIP_*_AUTH` variants); 3P provider active → `"auth: 3P provider active, skipping OAuth
refresh loop"`.

PoC: `pocs/auth-surface-audit.py` — read-only auditor: credential-file existence/mode/key
names/shapes, env-var **set/unset only (never values)**, platform keychain model. Exit 0.

## 2. HOW IT WAS FOUND

- Lane C4: the OAuth endpoint config block located as **one contiguous literal** (all URLs +
  client identities, 21:55–22:05); credential-file metadata read locally (paths, modes, key
  names — never values); `claude auth login --help` / `setup-token --help` introspection.
- Kills recorded: exact authorize-URL query string not recoverable from strings (constructed
  in minified JS); setup-token string prefix/length unisolated (metadata only by design).
- Trial (2026-10-18): `auth-surface-audit.py` → exit 0 with no values leaked;
  `stat ~/.claude/.credentials.json` → `600 519`, mtime 2026-10-19 — confirms mode 600,
  file exists, values untouched.

## 3. WHAT IT UNLOCKS

In plain terms: you now have the complete menu of every way the CLI can authenticate —
OAuth login, long-lived setup tokens, API keys via env or a helper script, enterprise
gateways, Bedrock, Vertex, Foundry — and where each credential lives on disk. If you build
tooling that runs the CLI on machines that are not yours, this is the map for choosing a
credential source that does not involve reading someone's personal keychain.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Credential-source selection:** for headless/CI, prefer in order:
  `ANTHROPIC_API_KEY` (env) → `apiKeyHelper` (stdout-only, printable-ASCII, TTL via
  `CLAUDE_CODE_API_KEY_HELPER_TTL_MS`) → `CLAUDE_CODE_OAUTH_TOKEN` (long-lived
  `setup-token`, `user:inference` scope) → provider env vars for Bedrock/Vertex/Foundry.
- **Audit harness:** run `pocs/auth-surface-audit.py` on any machine that runs the CLI —
  it reports credential-file presence/mode/key-names and env-set/unset without ever
  printing values, safe to log. (Note: `~/.claude/.credentials.json` on Linux is
  authoritative — no OS keychain.)
  ([pocs/auth-surface-audit.py](sandbox://workspace/rea-claude/deep-dive/pocs/auth-surface-audit.py))
- **apiKeyHelper pattern:** the script must print ONLY the key to stdout; gate on workspace
  trust; cache with the TTL env var; never rely on overriding `Authorization` via
  `ANTHROPIC_CUSTOM_HEADERS` (rejected — truncated evidence says it is invalid).
- **Bare mode:** `--bare` = strictly `ANTHROPIC_API_KEY` or `--settings`-supplied
  `apiKeyHelper`; OAuth and keychain never read; `/login` refused (`bareSignInRefusals`).
- **Enterprise:** `forceLoginMethod: gateway` + `forceLoginGatewayUrl` + `allowedProviders:
  ["gateway"]` in managed settings; Foundry uses `DefaultAzureCredential` with the
  `cognitiveservices.azure.com/.default` scope.
