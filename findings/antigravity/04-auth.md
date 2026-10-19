# 04 — Auth = Gemini Code Assist machinery; device flow + PKCE, 3 client IDs

**Trial status:** CONFIRMED. `a3_token_inspector.py` re-run exit 0 — zero secret bytes printed (shapes only); token was VALID at trial time (expiry 2026-10-18T23:33:46-04:00; a recent agy run had refreshed it — drift, not a PoC failure). `cloudcode-pa.googleapis.com` found 6× in the string table (spot-check CONFIRMED). `installation_id` file CONFIRMED present at `~/.gemini/antigravity-cli/installation_id`, 36 bytes, **mode 0640 (group-readable, not 0600 like the OAuth token)**. Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

Auth is vendored Gemini Code Assist machinery, not bespoke. Byte evidence:

- `*codeassistclient.CLIAuthProvider` / `IDEAuthProvider` / `HostAuthProvider`, `fileTokenStorage`, `compositeTokenStorage`, `refreshAndSaveStoredToken`, `ValidateStoredToken`.
- Backend: `cloudcode-pa.googleapis.com/Health`, `cloudcode-pa.googleapis.com/AgentPlugin`, with `v1internal` protos (`LoadCodeAssistRequest/Response`).
- Login = device flow first, PKCE browser second: `https://oauth2.googleapis.com/device/code`, `urn:ietf:params:oauth:grant-type:device_code`, prompt `"Please visit the following URL to authorize the applicat[ion]"`, plus vendored `golang.org/x/oauth2/pkce.go` (`TokenSourceWithPKCE`). Other endpoints: `https://accounts.google.com/o/oauth2/auth`, `https://oauth2.googleapis.com/token`, `https://sts.googleapis.com/v1/oauthtoken` (external-account path).
- **Three embedded OAuth client IDs (public identifiers; client-secret VALUES withheld):**
  - `1071006060591-tmhssin2h21lcre235vtolojh4g403ep.apps.googleusercontent.com`
  - `1098991175725-mdu1oe5cbbe1ckggsebobh94toiap657.apps.googleusercontent.com`
  - `884354919052-36trc1jjb3tguiac32ov6cod268c5blh.apps.googleusercontent.com`
  Two embedded client-secret values exist (`GOCSPX-` shape) — 3 IDs vs 2 secrets is an unexplained asymmetry (values never reproduced anywhere).
- Scopes (12): `aicode`, `cclogModel`, `cloud-platform`, `drive`, `drive.appdata`, `drive.apps.readonly`, `drive.file`, `drive.metadata`, `drive.metadata.readonly`, `drive.photos.readonly`, `experimentsandconfigs`, `userinfo.profile` (all `https://www.googleapis.com/auth/<scope>`).
- Token store is keyring-first, file-fallback. File: `~/.gemini/antigravity-cli/antigravity-oauth-token`, mode **0600**, 1669 bytes. Schema (field names only, verified by PoC): `{token: {access_token, refresh_token, expiry, token_type: "Bearer"}, auth_method: "consumer", id_token: <3-segment RS256 JWT>}`. Standard oauth2 token JSON + `auth_method` + Google id_token. Enterprise path: WIF provider (`wif_provider`), `enable_business_login`.
- **Name-trap documented:** `GetTokenBase` is NOT auth — it returns context-window budget (`GetMaxTokenBase`, `GetRemainingBudget`, `GetCustomizationTokenBase`). Real auth surface: `HasAuthToken{has_token, is_gcp_tos, location, project_id, wif_provider}` and `exa.host_bridge_pb.GetOAuthToken`.
- `installation_id`: 36-byte UUID at `~/.gemini/antigravity-cli/installation_id` (created at install, 2026-09-24); mirrored as `installation_uuid` in `jetski_state.pbtxt`; rides the wire as a proto field and telemetry key for `https://play.googleapis.com/log`. Rotation/deletion behavior: UNKNOWN (no rotation logic found).
- MCP OAuth: `CompleteMcpOAuthRequest{server_name, authorization_code}`; tokens stored in `mcp_oauth_tokens.json` — file does NOT exist on this box (schema from string constants only).

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A3 (auth/identity), strings/schema tier. Credential handling was metadata-only by constraint: PoC `pocs/a3_token_inspector.py` parses the user's own token file and prints only structure/expiry/mode. Command of record: `python3 pocs/a3_token_inspector.py` → `expiry: 2026-10-18T23:33:46.5661016-04:00`, `expiry_status: VALID`, `mode: 0o600 (owner-only)`. Trial spot-checks: `grep -cF cloudcode-pa.googleapis.com` → 6 hits; `ls -la ~/.gemini/antigravity-cli/installation_id` → 36 bytes, mode 0640. The a3 lane eureka: `GetTokenBase` is context-window budget accounting, not auth (~01:54).

---

## 3. WHAT IT UNLOCKS

Your login to the CLI is not a username and password — it is the same Google OAuth machinery as the IDE: a device code or browser flow hands you a token file, and that file is what the CLI presents to Google's backend on every call. The token file is locked to your user only (mode 0600), while the machine's install ID next to it is group-readable. And a method with "Token" in its name has nothing to do with login — it reports how much context window you have left. Knowing which is which keeps you from chasing the wrong door.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Auth-status probe (no secret needed):** `HasAuthToken` on the LS returns `{has_token, is_gcp_tos, location, project_id, wif_provider}` — the supported way to check login state.
- **Token file:** `~/.gemini/antigravity-cli/antigravity-oauth-token` — standard `golang.org/x/oauth2` JSON + `auth_method` + RS256 id_token. Handle per A3's metadata-only rule: parse shapes/expiry, never log secret bytes. Keyring is the primary store; file is fallback.
- **Refresh flow:** `POST https://oauth2.googleapis.com/token` with `grant_type=refresh_token`; failure surface: `"token refresh failed due to network error: %v"`.
- **Device flow:** `POST https://oauth2.googleapis.com/device/code` → poll with `urn:ietf:params:oauth:grant-type:device_code`; browser fallback uses PKCE (`ANTIGRAVITY_OPEN_URL` overrides the URL opener).
- **Enterprise:** Workload Identity Federation path via `wif_provider` + `enable_business_login`.
- **Identity triple the backend sees:** bearer access token + GCP project ID (`ANTIGRAVITY_PROJECT_ID`) + `installation_id` UUID. Do not reuse the OAuth token or `installation_id` across machines/identities.
