# 15 — Gateway full route table (18 paths)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287` · carved JS `~/workspace/rea-claude/deep-dive/carved/claude-bundle-full.js`
(offsets below are carved-bundle offsets, ~25840000–26100000 handler region)

> **Correction (2026-10-19):** the prior pass (`06-gateway-server.md`) knew 4 routes and described
> `/api/claude_code/settings` as a gateway route. It is NOT: it is the **client-side** remote-settings
> fetch URL (`qe()` builds `${e.url}/managed/settings` when a provider is set, else
> `${BASE_API_URL}/api/claude_code/settings`). The gateway itself serves `/managed/settings`. This doc
> corrects that conflation and publishes the full table.

---

## 1. WHAT WAS FOUND

The gateway (`claude gateway`) is a full HTTP server — `Bun.serve({hostname, port, idleTimeout:0, ...tls})`,
`maxHeaderSize=262144`, fallthrough `404 "not found"` — with an 18-path route table. The request router
keys on `Ot = new URL(le.url).pathname` and `le.method`.

| # | Path | Method gate | What it serves |
|---|---|---|---|
| 1 | `/` | GET only | Server-info JSON: `VERSION:"2.1.287"`, `BUILD_TIME:"2026-10-01T16:02:06Z"`, `GIT_SHA:"3c446a1b98aceb99a6cdee0f84a8bea42f4a8937"`, issue/readme URLs |
| 2 | `/.well-known/oauth-authorization-server` | any | RFC 8414 metadata: issuer, device_authorization_endpoint, token_endpoint, grant types (device_code urn + refresh_token), auth methods `["none"]`, scopes openid/profile/email, gateway_protocol_version |
| 3 | `/protocol` | GET | Embedded gateway protocol doc as `text/markdown; charset=utf-8` |
| 4 | `/oauth/device_authorization` | POST | RFC 8628 device flow; per-IP rate limit; returns device_code, user_code, verification_uri, expires_in, interval |
| 5 | `/device` | GET | HTML verification form (prefill user_code, idpOrigin) |
| 6 | `/device` | POST | CSRF gate (`sec-fetch-site`/origin vs gateway origin); rate limit; approves pending device_code → OIDC redirect |
| 7 | `/oauth/callback` | any | OIDC callback: code/state → nonce/browser-hash bind check → session mint (Set-Cookie) |
| 8 | `/oauth/token` | POST | grant_type ∈ device_code-urn → access+refresh tokens; refresh_token grant; slow_down/authorization_pending/access_denied per RFC 8628 |
| 9 | `/managed/settings` | any (session-bearer auth precedes) | Policy match → settings JSON + ETag; 404 "no policy matched"; desktop-session withholding unless policy has serve_to_desktop |
| 10 | `/api/oauth/usage` | GET | Usage query; 404 "not configured" |
| 11 | `/user/bootstrap` | GET | Requires `desktop:` block in matched policy else 404; serves bootstrap + header `x-gateway-spend-admin` |
| 12 | `/v1/models` | GET | Model list from matched policy's availableModels |
| 13 | `/v1/messages` | POST | Inference proxy; bearer-auth fast path; `x-load-test-user` (≤7 digits) impersonation; request metering + byte accounting |
| 14 | `/v1/messages/count_tokens` | POST | Same inference gate |
| 15 | `/v1/organizations/spend_limits` (+ prefix) | admin | x-api-key header or auth-header + admin_groups membership; spend-limits CRUD (`mb(e)=e===Ca||e.startsWith(Ca+"/")`) |
| 16–18 | `/v1/metrics`, `/v1/logs`, `/v1/traces` | POST | OTLP relay: map `vb={"/v1/metrics":"metrics","/v1/logs":"logs","/v1/traces":"traces"}` → fanout to targets |

Inference-path allowlist (verified literal): `AL=["/v1/messages","/v1/messages/count_tokens"]`,
`function jh(e){return AL.includes(e)}` — used both for the bearer fast path and the inference dispatch.

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Tool: `python3 re.finditer` windowed context mining on the carved bundle; `grep -aob` for path literals.

```
python3 -c "
import re
t=open('claude-bundle-full.js',encoding='utf-8',errors='replace').read()
rx=re.compile(r'Ot===(\"(?:/[^\"]*)\")')
for m in rx.finditer(t):
    if 25840000 <= m.start() <= 26100000: print(m.start(), m.group(1))"
# → 12 unique Ot=== paths (the router's direct equality matches);
# admin matcher (mb/Ca) and OTLP map (vb) found via re on their defs
```

Key handler evidence: `/` → `if(Ot==="/"&&le.method==="GET")return u0(...)` @25850603;
`.well-known/oauth-authorization-server` @25851639; `/protocol` @25852087; `/oauth/device_authorization`
@25852857; `/device` GET @25853882 / POST @25854021; `/oauth/callback` @25855791; `/oauth/token`
@25857678; `/managed/settings` @25860146; `/api/oauth/usage` @25862209; `/user/bootstrap` @25862346;
`/v1/models` @25863705; `/v1/messages` @25864272; `jh(Ot)` gate @25859664/@25863801; `AL=[...]`
@25685477; OTLP `vb` map @25775943, fanout @25863577; admin `mb` matcher @25759365;
fallthrough 404 @25866636. Path-string presence spot-confirmed by hand: `/v1/metrics` (5 hits),
`/v1/traces` (4), `/v1/organizations/spend_limits` (1), `/protocol` (12), `/oauth/device_authorization` (6).

## 3. WHAT IT UNLOCKS (plain language, no jargon)

This is not just an auth helper — it's a private API server that turns your machine into an Anthropic
endpoint: a client can discover how to log in (`/.well-known/...`), run a full device-code OAuth flow
(`POST /oauth/device_authorization`, verify at `/device`, mint session at `/oauth/callback`), fetch your
organization's managed settings, and then call the model through `/v1/messages` exactly like the public
Anthropic API — including a token-counting endpoint. Admins get a spend-limits control panel at
`/v1/organizations/spend_limits`. And there's a telemetry fan-in: anything can POST OpenTelemetry
metrics/logs/traces to `/v1/metrics|/logs|/traces` and the gateway relays them onward. If you deploy
this in a shared environment, every one of these is an exposed surface you must authenticate and audit.

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

- Route-gate any custom gateway wrapper against the allowlist: only `/v1/messages` and
  `/v1/messages/count_tokens` are inference paths (`jh()`); everything else is control plane. Block the
  control plane at the reverse proxy if you only want model access.
- Use `GET /` for version pinning in tooling: it returns VERSION/BUILD_TIME/GIT_SHA of the serving
  gateway — assert the expected build before routing traffic.
- The OTLP fanout (`/v1/metrics|/logs|/traces`) is a ready-made local collector endpoint; point any
  OTEL-instrumented process at the gateway and it relays upstream. Watch the admin header
  `x-gateway-spend-admin` on `/user/bootstrap` for spend-admin flows.
- CSRF lesson for your own device flow: `/device` POST gates on `sec-fetch-site`/origin vs the gateway
  origin — copy that check, plus the per-IP rate limits (`rate_limits.device_authorization`,
  `rate_limits.device_verify`), into any internal device-verification UI.
- Do NOT put `/api/claude_code/settings` behind the gateway (it was never a gateway route): remote
  settings are served from `/managed/settings` with session-bearer auth preceding the policy match.
