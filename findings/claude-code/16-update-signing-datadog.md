# 16 — Update signing (RSA-4096), Datadog sink, event logging, master kill switch

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287` · carved JS `~/workspace/rea-claude/deep-dive/carved/claude-bundle-full.js`
(offsets below are carved-bundle offsets)

---

## 1. WHAT WAS FOUND

**Update flow:** version checks hit `https://downloads.claude.ai/claude-code-releases/<channel>` (plain-text
version, 3 attempts); release binaries come from `downloads.claude.ai`, the update feed from
`releases.claude.com` (`YP.VM_BUNDLE_HOST="downloads.claude.ai"`, `YP.UPDATE_FEED_HOST="releases.claude.com"`).
Every release manifest is RSA-SHA512 signed: the CLI fetches `manifest.json` (≤1MB) plus sidecar
`manifest.json.raw-sig.json` (≤64KB), verifies `RSA-SHA512(Buffer.concat([sidecarBytes, manifestBytes]))`
against an embedded public key, and refuses the update on `signature_invalid` / `key_mismatch` /
`version_mismatch`. Signature enforcement itself is GrowthBook-gated (`tengu_elegant_pancake` → modes
always/true). A 404 on the sidecar is `sidecar_missing` unless the legacy `allow-unsigned-legacy` policy
applies (then checksum-only with an `update_manifest_signature:unsigned_legacy` warning).

**Release-signing public key (RSA-4096 SPKI), full value extracted** — the compiled trust root for BOTH
update manifests and the served model catalog (`https://downloads.claude.ai/model-catalog/v1/catalog.json`,
same key id `claude-code-release-signing-key`; `SHA256(SPKI-DER)` pin `publicKeySha256` checked byte-wise):

```
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAp28rSV5I8HmK8CK9GixBUZR/gtJxeOCsRXO4EJiej40jzBmQA3cWXGosVO82ZfFsRKVTtMC5iB/HH9sxjncrmYNWGroJNbx29m/FgYQBgkCXT4AfFl6rnnXqRGLZOerj/4AqE4yQ1GZbhBgR55Z7ro0ieKK8RHYUspBKAFHyWRhCCz6THW6YRbf0p/hG/08TOY6Sj3cJ7/AEoTRf9ZmVNX1k0KvbUSiVGpGY9OIHWgxRJUF2pArU4o/hk+sqGAgEUh8Bjvjwvz6+quLXPg+y0Y8Ugb1Fg6BUppam/zydYY/Q/+yNjnuF154gD1jEeeir8R5czs6zUHSbo2yXUpAsIdWYo5End8vGsluVmFExnUWm/fTVMGoM5Wm3v1VRepMydEnJ+atz4oQdmPQcKNAip5GJO2uyk++xFr9CpKvlR5jral92toYV/m+mur3va8ydamWBo/qG7/wt0sdS81IwH6lcu0SQ39rgKD+bdoPLv05EqVMYTFRI2QZEsWGYTMs0DOrfCIJFH50qyD0x4sWw1gEWeG3jDgY8cj2StZz+zjqzUd05CibcCzEAGm1EQg5y9D40tIsAU1OI7bpgQ9V0lC8lrqE7zJY66UK9Z1daA8jrdDi6migNjHFrXfT3V4QvMthCIO05q05SS3x2G3ZpIgmI+CePUPB1pDf+lhPkU1MCAwEAAQ==
```

`SHA256(SPKI-DER) = 89a24e2e18d2f8fa4627a0a47cf76c3682aef237b60d2cd115d6f5202e2e9896`
(public verification key by design; no private material). Full value also saved at
`~/workspace/re-suite/findings/claude/release-signing-key-spki-b64.txt` (quoted verbatim from that file).

**Datadog error-log sink:** `https://http-intake.logs.us5.datadoghq.com/api/v2/logs` with embedded
**public** client token `pubea5604404508cdd34afb69e6f42a05bc` (sent as `DD-API-KEY` header; `pub`-prefixed
= client token by design), batch 100 / 15s timeout / 5s flush. Browser variant:
`https://browser-intake-us5-datadoghq.com/api/v2/logs` (batch 25, 10s). Init gated by the master kill
switch; events pass an allowlist + redaction, and require firstParty context.

**1P event logging:** `https://api.anthropic.com/api/event_logging/v2/batch` — 10s interval, 200 events per
export, queue cap 8192, shutdown flush budget 2s, up to 8 retry attempts with backoff (500ms → 30s).
Server-overridable via the `tengu_1p_event_batch_config` gate. Failed batches persist locally to
`~/.claude/telemetry` (`1p_failed_events.<sha256-base64url>` filenames).

**Master kill switch** (verbatim): `function Eh(){return u()||uo()!==null||gL()||l()}` @1485184, where
`gL()` is `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` / `DISABLE_TELEMETRY` env mapping and `l()` is
`CLAUDE_CODE_CUSTOM_OAUTH_URL` set. `K2(){return!Eh()}` gates every 1P emit and the Datadog init; a
server-side kill runs through `S_t("firstParty")` / the `tengu_frond_boric` config.

**KILLS:** no embedded private keys — every `-----BEGIN PRIVATE KEY` hit is code (WebCrypto pkcs8 error
string; gateway `oidc.client_assertion.private_key_pem` validation messages for user-supplied config).
No embedded certificates — all `BEGIN CERTIFICATE` hits are parser regexes or validation strings
(client-cert loader, node-forge, msal, gateway OIDC, CA-bundle pointer scan, cert-block validator). No
literal certificate bytes anywhere.

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Tool: `grep -aob` + `dd` on the carved bundle; `python3 re` for signature/endpoint anchors; the SPKI
value re-quoted from `~/workspace/re-suite/findings/claude/release-signing-key-spki-b64.txt`.

```
grep -aob 'api/event_logging/v2/batch' claude-bundle-full.js
# → 3302325 (Ec constructor @3302455 region: endpoint = baseUrl + path default)

grep -aob 'datadoghq.com/api/v2/logs' claude-bundle-full.js
# → 7340807  (http-intake; browser variant @7353560)

grep -aob 'pubea5604404508cdd34afb69e6f42a05bc' claude-bundle-full.js
# → 7340839 (var pXn="pubea5604404508cdd34afb69e6f42a05bc"; H(e) posts {"DD-API-KEY":pXn})

dd if=claude-bundle-full.js bs=1 skip=1485184 count=90
# → function Eh(){return u()||uo()!==null||gL()||l()}

dd if=claude-bundle-full.js bs=1 skip=24523900 count=160
# → ...e.indexOf("-----BEGIN PRIVATE KEY...  (WebCrypto pkcs8 error string, not a key)

dd if=claude-bundle-full.js bs=1 skip=25733950 count=150
# → message:'oidc.client_assertion.private_key_pem is not a PEM private key...
#   (gateway validation message for user-supplied config)

dd if=claude-bundle-full.js bs=1 skip=36724720 count=100
# → ...if(Oe.includes("-----BEGIN CERTIFICATE-----")&&!cYr.test(Oe))...
#   (CA-bundle scan predicate, not a cert)
```

Update/signature machinery per lane doc: `je()` manifest verifier @12401350, `tt()` fetch @12407340,
`qSe()` suppression @3396761, catalog constants @15862566–15866541 (SPKI literal @15862566; `ze()` PEM
form @12399915). Offset note: Datadog/token offsets are current-carve; earlier lane drafts cite the same
artifacts ±~30 B from a superseded carve.

## 3. WHAT IT UNLOCKS (plain language, no jargon)

Your CLI's update pipeline is locked to one key: the 4096-bit public key above is the only thing the CLI
trusts to approve new versions. If Anthropic signs a release with the matching private key, your machine
installs it; anything else gets rejected with a loud error. That means the *supply chain* is strong —
nobody can slip your CLI a fake update without that private key — but it also means Anthropic alone
decides what your next version is, since only their key counts. Meanwhile, every crash report and
sampled error event your session generates flows to Anthropic's Datadog, authenticated with a public
token baked into the binary — the token is meant to be public, but it lets anyone map which Datadog
tenant collects Claude Code's errors. And the master kill switch is real and documented: one environment
variable (`DISABLE_TELEMETRY`) silences the whole reporting stack.

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

- Verify any release independently: download `https://downloads.claude.ai/claude-code-releases/<channel>/<version>/manifest.json`
  + `manifest.json.raw-sig.json`, base64-decode the SPKI above into a PEM, and run the same check the CLI
  does — RSA-PKCS1-v1_5-SHA512 over `sidecarBytes || manifestBytes`, with the SPKI-SHA256 pin
  `89a24e2e…e9896`. Mismatch means do not install.
- Pin before trusting: the CLI enforces this on its own path; if you distribute the CLI inside your own
  installer, gate on the same `je()` semantics (sidecar present, `version_mismatch` and `key_mismatch`
  both fatal) rather than checksum-only.
- Telemetry lockdown for fleet machines: `DISABLE_TELEMETRY=1` (or `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1`)
  kills 1P event logging, exposure logging, and the Datadog sink; OTLP export is opt-in anyway
  (`CLAUDE_CODE_ENABLE_TELEMETRY` + exporter env). Confirm quietness by watching for `~/.claude/telemetry`
  writes — presence of `1p_failed_events.*` files means exports were attempted and failed.
- Do not extract and reuse the Datadog `pub…` token for your own log shipping — it is scoped to
  Anthropic's tenant and rate-limited as a client token; treat it as infrastructure telemetry, not a key.
