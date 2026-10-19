# 06 — `claude gateway` is a full HTTP server in the binary (C2)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C2 (cloud/gateway) · **Trial status:** CONFIRMED live (`claude --help` lists
`gateway [options]  Run the enterprise auth/telemetry`; `pocs/cloud_mapper.py` re-run → exit 0,
291 values incl. `gateway_keys: 6`)
**Confidence:** CONFIRMED (byte-level). **KILL (corrects prior art):** "gateway is auth/telemetry only" —
it also proxies inference and serves managed settings/policy.

---

## 1. WHAT WAS FOUND

`claude gateway --config <path>` runs `startGateway` — an HTTP server implemented **in this
binary** (entry chunk-hyp9w8x4.js, `drainOnSignal`). Served routes (verbatim):

- `/oauth/token` (grant_types `device_code` + `refresh_token`; issues access/refresh tokens,
  ttl `r.session.ttl_hours`), `/oauth/callback`
- `/managed/settings`, `/api/claude_code/settings`, `/user/bootstrap`

It is NOT auth/telemetry-only: the string "customer-routed inference is temporarily
unavailable: the gateway cannot obtain current verification keys" **confirms the gateway
proxies inference upstream**, with a `mantle` Bedrock upstream. It also carries Postgres
migrations (`CREATE TABLE IF NOT EXISTS _migrations`, `SELECT pg_advisory_lock(6775156)`)
and k8s notes (NetworkPolicy; "pod can reach cloud metadata endpoint (169.254.169.254);
apply egress NetworkPolicy") — it is designed to run in Kubernetes.

Byte-level evidence:

- Config schema keys seen: `oidc` (discovery_url, issuer, client_id, client_secret,
  token_endpoint_auth_method, id_token_signed_response_alg, clock_skew_seconds,
  service_account_json_path, admin_email, google_groups), `jwt_secret`, `postgres_url`,
  `max_connections`, `read_keys`, `write_keys`, `blocked_message`, `audit_retention_days`,
  `spend_retention_months`, `load_test_mode` ("requests are built and signed but not sent
  upstream, and clients get a canned reply"), `mantle` upstream provider ("Amazon Bedrock's
  Mantle endpoint"), `modelDiscoveryEnabled` ("Auto-populate the model picker from the
  provider's model-list endpoint at launch").
- Client side: `CLAUDE_CODE_USE_GATEWAY=1` + `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`
  routes a session through the gateway; missing/invalid → "CLAUDE_CODE_USE_GATEWAY is set
  but ANTHROPIC_BASE_URL is missing ... ; ignoring". `allowedProviders` must list
  `"gateway"`; `forceLoginMethod: "gateway"` + `forceLoginGatewayUrl` (managed-settings only)
  drives gateway sign-in: "Your organization's gateway URL (set by managed settings):",
  "Trust gateway <url>?", "The TLS certificate for this gateway has changed since you last
  connected. Only continue if your administrator has confirmed a certificate rotation."
- `gatewayInternalNetworks`: IPv4 CIDR blocks, "first-address/prefix, /0 to /32 … must not
  overlap private address space ('declare only the public block your network is numbered
  from')"; invalid → "gateway sign-in governed by this source is refused until it is fixed."
- `serve_to_desktop`: per-policy opt-in in the gateway's managed-settings policy
  ("the gateway at ${url} has no Claude Code policy for this Desktop session … check
  serve_to_desktop for this user's policy"). Error tokens: `gateway_signin_required`,
  `gateway_session_expired`.

## 2. HOW IT WAS FOUND

- Lane C2: string-table extraction + windowed-context mining; the gateway routes, config
  keys, OIDC schema, and inference-proxying string were all found as byte-verbatim quotes
  (scratchpad-c2.md; endpoint table in `pocs/cloud-map/cloud-map.md`).
- The gateway YAML schema was reconstructed from validation/zod strings (field optionality
  partial — LIMITATION); the `--help` text ("Run the enterprise auth/telemetry gateway")
  is what the prior art's auth/telemetry-only reading rested on, and the inference-proxy
  string kills it.

## 3. WHAT IT UNLOCKS

In plain terms: the gateway is a self-hostable enterprise control plane, not a telemetry
pipe. An organization can run its own gateway between its developers and the model —
owning auth, policy, and even the inference path — while the CLI stays the same binary
on everyone's machine.

## 4. HOW A DEVELOPER BUILDS ON IT

- **Self-hosted enterprise gateway:** `claude gateway --config <path>` with the recovered
  config schema (oidc, postgres_url, read/write keys, retention windows) — deploy in k8s
  per the embedded NetworkPolicy guidance; flip `load_test_mode` for signed-but-canned
  dry runs.
- **Client enrollment:** distribute `CLAUDE_CODE_USE_GATEWAY=1`, `ANTHROPIC_BASE_URL`,
  `ANTHROPIC_AUTH_TOKEN` to clients; pin `forceLoginMethod: "gateway"` +
  `forceLoginGatewayUrl` + `gatewayInternalNetworks` in managed settings
  (`/etc/claude-code/managed-settings.json`) so sign-in is policy-driven, not per-user.
- **Policy seam:** the gateway serves `/managed/settings` and `/api/claude_code/settings` —
  the point where org-wide policy/telemetry/model-routing can be injected without touching
  any developer's machine. The `forceLoginOrgUUID` / `allowedProviders: ["gateway"]`
  managed keys complete the lockdown.
- **Gateway key lineage:** `CLAUDE_CODE_HOST_GATEWAY_LINEAGE` env var exists (semantics
  ungrounded) — worth probing when building gateway-routed tooling.
