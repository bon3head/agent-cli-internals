# 13 — GrowthBook is the experiment SDK (NOT Statsig)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287` · carved JS `~/workspace/rea-claude/deep-dive/carved/claude-bundle-full.js`
(offsets below are carved-bundle offsets)

> **Correction (2026-10-19):** this REPLACES the experiment-plane story told in `11-experiment-gates.md`.
> The prior pass inventoried `tengu_*` gate *names* but misattributed the plane; the SDK is GrowthBook, not
> Statsig. The prior "128 gates" figure is lossy and unreproducible — no 128-list artifact exists on disk.
> The prior "528" figure missed 21 real gates (including `tengu_kairos_cron`).

---

## 1. WHAT WAS FOUND

Every `tengu_*` feature gate in the CLI is a **GrowthBook feature evaluation**, served by a vendored
GrowthBook JS SDK embedded in the bundle. There is no Statsig SDK in the binary — the string `statsig`
occurs only as a directory name (`~/.claude/statsig`, 4 hits), never as SDK code.

The SDK client is instantiated with an **embedded SDK client key** (public-by-design) and **remoteEval**
against Anthropic's own API host:

```
g="sdk-zAZezfDKGoZuXXKe"; h=Tu();
new ts({apiHost:h, clientKey:g, attributes:s, remoteEval:!0,
        cacheKeyAttributes:["id","organizationUUID","slackTagConnected","atisPin","ccrDerivedSurface"],
        apiHostRequestHeaders:{"User-Agent":Do(),...v&&n.headers},...!1})
```

with `function Tu(){return"https://api.anthropic.com/"}`. So all 549 distinct gate checks resolve
**server-side**: the CLI sends user/device attributes and receives evaluated gate values back — the
client never sees the full ruleset, so no config inspection or local flag file reveals gate state.

Gate count: **549 distinct `tengu_*` gate names**, enumerated as the union of double-quoted literals at
two gate-check call sites — `C("tengu_*",…)` (544) and `iB("tengu_*",…)` (7, of which 5 are not checked
via `C`). `iB` is a true alias: `function iB(e,n,r){return C(e,n)}`, and `C(e,n){return Uo(e,n).value}`
where `Uo(e,n){return Ke().getFeatureValueWithSource(e,n)}` — the GrowthBook `getFeatureValue` path.
Refresh cadence is itself a gate: `tengu_gb_refresh_interval_minutes`, default 360 minutes. A hard env
kill exists: `DISABLE_GROWTHBOOK` (also in the 41-name env inventory), plus `Pb(){return!a.DISABLE_GROWTHBOOK&&K2()}`.

What is sent to the eval endpoint (user-attribute inventory, `$wn()`): device id, session id, platform,
apiBaseUrlHost, organizationUUID, accountUUID, userType, subscriptionType, rateLimitTier,
organizationRole, subscriptionCreatedAt, firstTokenTime, **email**, appVersion, releaseChannel
(autoUpdatesChannel), entrypoint, sessionOrigin, `ccrDerivedSurface`, atisPin, hasUsedRemoteSession,
hasRemoteEnvironment, slackTagConnected. Experiment exposures are logged back as 1P events
(`GrowthbookExperimentEvent` with experiment_id/variation_id) via the event-logging pipeline.

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Tool: `grep -aob` + `dd` byte-window reads on the carved bundle; `python3 re` for enumeration.

```
grep -aob 'sdk-zAZezfDKGoZuXXKe' claude-bundle-full.js
# → 2981543:sdk-zAZezfDKGoZuXXKe

dd if=claude-bundle-full.js bs=1 skip=2981500 count=900
# → ...this.usedNonDefaultHost||=h!=="https://api.anthropic.com/";
#    let S=new ts({apiHost:h,clientKey:g,attributes:s,remoteEval:!0,
#    cacheKeyAttributes:["id","organizationUUID","slackTagConnected","atisPin","ccrDerivedSurface"],
#    apiHostRequestHeaders:{"User-Agent":Do(),...v&&n.headers},...!1})...

dd if=claude-bundle-full.js bs=1 skip=2973590 count=120
# → function Tu(){return"https://api.anthropic.com/"}

dd if=claude-bundle-full.js bs=1 skip=3325683 count=260
# → function iB(e,n,r){return C(e,n)}async function v_(e){return Ke().checkGateCachedOrBlocking(e)}...
# (C→Uo→Ke().getFeatureValueWithSource chain per lane doc @3325483–3325543)

python3 -c "
import re
t=open('claude-bundle-full.js',encoding='utf-8',errors='replace').read()
c=set(re.findall(r'C\(\"((?:tengu_)[a-z0-9_]+)\"',t))     # GrowthBook eval sites
b=set(re.findall(r'iB\(\"((?:tengu_)[a-z0-9_]+)\"',t))    # iB alias sites
print(len(c), len(b), len(c|b))                            # 544 7 549
print('tengu_kairos_cron' in c|b)                          # True
"
```

The prior 528-list missed `iB`-only gates such as `tengu_kairos_cron` and `tengu_kairos_cron_durable`
(checked at @7616076/`_H()` — `function _H(){return!a.CLAUDE_CODE_DISABLE_CRON&&iB("tengu_kairos_cron",!0,t)}`).

Offset note: carve-boundary drift — earlier lane drafts cite this region at @2982069; the current carve
has the literal at 2981543 and the `new ts({` constructor around 2981600. Same bytes, shifted carve.

## 3. WHAT IT UNLOCKS (plain language, no jargon)

Anthropic can flip any of 549 switches on your CLI without shipping an update — turn features on for 5%
of users, roll back a broken feature in minutes, or A/B test a behavior on your machine while your
neighbor's stays the same. Because evaluation happens on Anthropic's servers ("remoteEval"), you cannot
see the rulebook: there is no local file to read that tells you which gates are on for you, only the
result your session was given. On every evaluation, the CLI sends Anthropic a profile bundle that
includes your email, subscription type, and organization identity — that's the price of admission for
each gate check. For a security review this is a live remote-control plane inside the product: 549
knobs, all server-driven, all invisible locally, one kill switch (`DISABLE_GROWTHBOOK`) and one
disable env var each for the whole telemetry stack.

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

- Reproduce the 549-gate list: run the python one-liner above, save `sorted(c|b)` to a text file. That is
  now the canonical gate inventory; diff it against any future version's output to see added/killed gates.
- Opt out per session: `DISABLE_GROWTHBOOK=1 claude` — `Pb()` short-circuits the SDK. Combine with
  `DISABLE_TELEMETRY=1` to also stop the exposure-event logging (`E4o` is gated by `K2()`, which feeds on
  the same master kill switch as 1P telemetry).
- Observe gates flipping: `tengu_gb_refresh_interval_minutes` defaults to 360 min; set it server-side is
  not possible locally, but you can force a re-fetch by restarting the CLI (init path runs
  `refreshGrowthBookFeatures`/`startPeriodicRefresh`).
- Network-level view: the remoteEval request goes to `https://api.anthropic.com/` (non-default-host use is
  tracked via `usedNonDefaultHost`), headers include `User-Agent` + the session's Authorization bearer.
  A MITM proxy (with the box's CA) shows the evaluated payload shape.
- Watch for the `GrowthbookExperimentEvent` 1P events to see which experiments your session was enrolled
  in — `event_type:"GrowthbookExperimentEvent"`, fields `experiment_id`, `variation_id`.
