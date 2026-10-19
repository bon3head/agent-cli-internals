# 12. BYO model path: `AGY_LLM_GATEWAY_*` env vars

**Trial status:** CONFIRMED. `AGY_LLM_GATEWAY_URL` spot-check found as an env-var log string (`AGY_LLM_GATEWAY_URL%s is malformed: %w`: consistent with the documented-by-strings verdict). Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

The binary embeds a complete custom-model-gateway configuration surface as environment variables: the sanctioned way to point the CLI at a non-Google backend (CONFIRMED, strings tier):

| Variable | Purpose |
|---|---|
| `AGY_LLM_GATEWAY_URL` | gateway endpoint URL |
| `AGY_LLM_GATEWAY_API_KEY` | auth for the gateway |
| `AGY_LLM_GATEWAY_HEADERS` | extra request headers |
| `AGY_LLM_GATEWAY_CA_CERT` | custom CA certificate |
| `AGY_LLM_GATEWAY_PROXY_URL` | proxy for gateway traffic |
| `AGY_LLM_GATEWAY_MODELS` | model list to expose |
| `AGY_LLM_GATEWAY_TIER_FLASH` | flash-tier model id |
| `AGY_LLM_GATEWAY_TIER_FLASH_LITE` | flash-lite-tier model id |
| `AGY_LLM_GATEWAY_TIER_PRO` | pro-tier model id |
| `AGY_LLM_GATEWAY_WIRE_PROTOCOL` | wire protocol for discovery |

Byte evidence: the full variable set appears in an env-var enumeration; the trial spot-check confirmed `AGY_LLM_GATEWAY_URL%s is malformed: %w` as a format-string log line; i.e. the CLI actually reads and validates this var at runtime.

This plugs into the Tier 3 slot of the 4-tier resolution waterfall (see finding 03):

```
Tier 1 (Inline admin_settings models.list)
→ Tier 2 (Remote catalog)
→ Tier 3 (Gateway discovery at %s, wireProtocol: %s)
→ Tier 4 built-in default
```

Custom gateway models consume `MODEL_PLACEHOLDER_M*` slots: `[ModelConfig] %d custom gateway model(s) exceeded the maximum placeholder limit` is the overflow signal. There is also a prompt-template branch keyed on a reasoning-class placeholder set `{M54, M43, M16, M37, M36, M34, M33}`: an alternate prompt path for reasoning models.

**Scope verdict:** documented-by-strings. Exact wire protocol values and per-field behavior unverified at this tier (no live gateway tested).

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A5 (internal intel), ~02:20. The gateway env-var family was found while decoding the `[ModelConfig]` resolution log strings (:347310/:347249); the 4-tier waterfall and Tier 3 discovery message came from the same block. Trial re-verified `AGY_LLM_GATEWAY_URL` as a live-read env var via its format-string log line.

---

## 3. WHAT IT UNLOCKS

The CLI does not have to talk to Google's models: hidden in the program is a full set of settings for pointing it at your own model server instead. Give it the URL, the API key, and which of your models plays each role (the fast one, the cheap one, the strong one), and it will route through your backend in place of Google's, sitting at a documented tier in the model's decision chain. It is the officially-shaped escape hatch for anyone who wants the agent without Google's serving.

---

## 4. HOW A DEVELOPER BUILDS ON IT

```bash
export AGY_LLM_GATEWAY_URL="https://my-gateway.internal/v1"
export AGY_LLM_GATEWAY_API_KEY="<key>"
export AGY_LLM_GATEWAY_HEADERS='{"X-Team":"agents"}'   # exact format unverified
export AGY_LLM_GATEWAY_WIRE_PROTOCOL="<proto>"         # exact values unverified
export AGY_LLM_GATEWAY_MODELS="my-flash,my-pro"
export AGY_LLM_GATEWAY_TIER_FLASH="my-flash"
export AGY_LLM_GATEWAY_TIER_FLASH_LITE="my-flash-lite"
export AGY_LLM_GATEWAY_TIER_PRO="my-pro"
export AGY_LLM_GATEWAY_PROXY_URL="http://proxy:3128"  # optional
export AGY_LLM_GATEWAY_CA_CERT="/path/ca.pem"         # optional
agy
```

- Verify resolution with the Tier 3 log line: `[ModelConfig] ... Tier 3 (Gateway discovery at %s, wireProtocol: %s)`.
- Overflow: watch for `... exceeded the maximum placeholder limit`; custom models consume `MODEL_PLACEHOLDER_M*` slots.
- Caveats: exact `WIRE_PROTOCOL` vocabulary and `HEADERS` format are unverified at strings tier; probe Tier 3 discovery logging against a test gateway to pin them down. Combined with Tier 1 (inline `admin_settings models.list`) you can bypass the server catalog entirely.
