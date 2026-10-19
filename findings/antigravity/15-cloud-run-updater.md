# 15. Cloud Run auto-updater: the real update host

**Trial status:** CONFIRMED. The update check goes to a Cloud Run endpoint, not GitHub releases. This weakens-to-killed the prior inference (doc 11) that "update artifacts likely download via GitHub releases."

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 1. WHAT WAS FOUND

**The CLI's update check host is `https://antigravity-cli-auto-updater-974169037036.us-central1.run.app`** @92337300 (Cloud Run, project number 974169037036, us-central1). The GitHub-releases inference is dead on arrival:

- `github.com/google-antigravity` appears exactly **twice** in the 221MB binary: both inside EMBEDDED DOCS (@28422339, @28439424: sdk.md references to the public `antigravity-sdk-python` repo). Zero update-host relevance.
- 12 total `/releases/` string hits, all unrelated (yarn, extjs, ASP.NET, rpmfusion): none point at an agy artifact.
- The public CHANGELOG URL (`https://raw.githubusercontent.com/google-antigravity/antigravity-cli/refs/heads/main/CHANGELOG.md`) is re-confirmed, but it is **changelog fetch only**.
- The binary's own download URL is composed at runtime / not in cleartext: **download host UNVERIFIED**. The Cloud Run app is the manifest/check host; where the tarballs come from is still open.

**Update engine mechanics (all CONFIRMED):**

- **Lock semantics:** `updater.ttlStillFresh` + `flock.TryLock` on a file lock (`update.lock` present) with state file `update_status.json`. Cooldown message: `Last check was less than 15 minutes ago, skipping update (under lock)`; a 15-minute TTL gate on update checks.
- **Full engine API** (`google3/third_party/jetski/cli/updater/updater`): `CheckForUpdate` @0x92ae4a0, `TriggerUpdateAndRelaunch` @0x92ae6c0, `checkManifest` @0x92addc0, `isNewerVersion` @0x92adcc0, `GetManifestURLFromBase` @0x92a9040, `ttlStillFresh` @0x92a91c0, `triggerUpdateShared` @0x92a9240, `runUpdateShared` @0x92aa780, `writeStatus` @0x92ad1c0, `waitForUpdateStatus` @0x92aefc0, `relaunchProcess` @0x92af220, `extractTarGzMember` @0x92ad740, `resolveAppDataAndUpdaterPaths` @0x92a8ea0, `renameWithRetry` @0x92a8c00, plus `updater.prepareBgCommand`; **background re-exec**: an update triggers a detached re-launch of the new binary, not an in-process swap.
- **Client reports its update channel to the server:** `ClientMetadata.update_channel` (google.internal.cloud.code.v1internal, proto field @94912307, getter @23916652). `ReleaseChannel` also exists on `OnboardUserStatus` (@94910391). But: **no "stable"/"beta"/"insiders" channel VALUE strings for the CLI updater exist in the binary** (3x update_channel, 15x release_channel, 8x updateChannel hits all exhausted; kill switch: `AGY_CLI_DISABLE_AUTO_UPDATE` @26281194, read-path unverified; prior kill stands). `insiders` appears only in the embedded `jetski-insiders` tarball-fetch script @29166821–29166927: that's the VS Code/IDE channel, not the CLI.

**Dated correction (2026-10-19):** doc 11's "INFERENCE: update artifacts likely download via GitHub releases from that org" is withdrawn — evidence now shows the check host is the Cloud Run URL and GitHub hosts only the changelog. The download host remains UNVERIFIED; do not cite GitHub releases as the update source.

---

## 2. HOW IT WAS FOUND

Lane DEPTH-INTEL (strings tier) + DEPTH-GORESYM (symbol recovery), both against the sha256-verified binary.

- `sha256sum /home/hatch/.local/bin/agy` -> `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`
- `strings -a -t d /home/hatch/.local/bin/agy > agy.strings.txt` (1,924,440 lines)
- Check host: `grep -F 'https://antigravity-cli-auto-updater-974169037036.us-central1.run.app' agy.strings.txt` -> @92337300 (single hit; adjacent to the update-lock message string)
- Lock: `grep -F 'Last check was less than 15 minutes ago, skipping update (under lock)' agy.strings.txt` + `grep -o 'flock.TryLock\|update.lock\|update_status.json\|updater.ttlStillFresh' agy.strings.txt`
- GitHub kill: `grep -cF 'github.com/google-antigravity' agy.strings.txt` -> 2 (both embedded-docs); `grep -cF '/releases/' agy.strings.txt` -> 12 (all unrelated, enumerated)
- Channel fields: `grep -F 'update_channel' agy.strings.txt` -> 3 hits; field @94912307, getter @23916652 from pclntab scan; `grep -cF 'release_channel' agy.strings.txt` -> 15; `grep -F 'insiders' agy.strings.txt` -> embedded script @29166821–29166927
- Engine symbols: pclntab scan for `google3/third_party/jetski/cli/updater/updater.(*` (DEPTH-GORESYM §3, addresses @0x92a8ea0–0x92af220)

---

## 3. WHAT IT UNLOCKS

Here's the deal: the program doesn't check GitHub for updates the way its public changelog would suggest. It phones home to a Google-run Cloud Run service that decides whether a newer build exists, and nobody outside Google has seen what the actual download host is, because the binary builds that URL at runtime. Updates are also throttled: the program refuses to check more than once every 15 minutes, enforced by a file lock. When an update does land, the old binary re-launches the new one in the background rather than hot-swapping itself. And the CLI tells Google's servers which update channel it's on, even though no channel names like "stable" or "beta" appear anywhere in the binary, meaning the channel value is either a default compiled in or assigned server-side. Practically: auto-updates are a server-driven pipeline, not a public GitHub artifact you can mirror or pin.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Watch for updates:** the Cloud Run check host (`https://antigravity-cli-auto-updater-974169037036.us-central1.run.app`) is the live signal, not the GitHub org: the CHANGELOG at `https://raw.githubusercontent.com/google-antigravity/antigravity-cli/refs/heads/main/CHANGELOG.md` is fetch-only, do not treat it as the release feed.
- **Local update state:** read `update_status.json` in the app-data dir (paths via `updater.resolveAppDataAndUpdaterPaths` @0x92a8ea0): it holds the last-check state the 15-min TTL gates on.
- **Disable auto-update:** `AGY_CLI_DISABLE_AUTO_UPDATE` (env var string present @26281194; read-path unverified: verify at runtime before relying on it).
- **Manifest URL composition:** `updater.GetManifestURLFromBase` @0x92a9040 builds the manifest URL from the Cloud Run base: the single function to instrument to learn the download host; the host itself is not in cleartext.
- **Update flow hooks:** `CheckForUpdate` @0x92ae4a0 (entry), `isNewerVersion` @0x92adcc0 (version compare), `TriggerUpdateAndRelaunch` @0x92ae6c0 + `relaunchProcess` @0x92af220 (background re-exec semantics: a re-launched process, not an exec-in-place).
- **Channel reporting:** `ClientMetadata.update_channel` (v1internal, field @94912307) is sent to the server with requests: if you need to know what channel a client claims, capture it there; do not expect "stable"/"beta"/"insiders" literals in the binary (they are absent, confirmed by exhaustive search).
