# Methodology

Everything in this repo came from reading the programs' own files, not from running them against live services. Three different toolchains needed three different instruments; the adjudication and constraint discipline held the whole thing together.

> **Systemic lesson (2026-10-19, reinforcement):** packed-string-run tokenizing is a **LOSSY counting
> method** and caused every major count error in the first pass (claude 199→183 keys, 1965→2133
> manifest rows, "128" gates→549 names; codex 97/101→101/101 fields; agy 341→348 methods). Go strings
> are length-prefixed, not NUL-terminated, so adjacent table entries run together at the byte level
> and naive token boundaries are wrong. The correct methods, per target:
> - **codex (Rust/serde):** the actual `FIELDS: &[&str]` statics — 101 consecutive `(ptr,len)` pairs @0xfcc98c0 (byte-identical duplicate @0xfe370d0). Ground truth, not heuristics.
> - **agy (grpc-go):** `Unimplemented*Server` codegen symbols (`(*Unimplemented<Svc>Server).<Method>`) — one symbol per RPC, immune to string-concat artifacts.
> - **claude (Bun):** fresh re-carves with independent parsers + `reverify` claim gates on exact offsets.
> Any count in this repo derived from packed runs is flagged; counts from the three methods above are the ones to trust.

## Techniques per target

### Antigravity CLI (Go, stripped, Google-internal toolchain)

**Go pclntab parsing.** The stock Go function-table parser failed: the Google-internal go1.28 layout differs from upstream (`textStart=0`). A magic scan found a candidate table at file offset `0x1512750` with `nfunc=164366` but a non-upstream header. Brute-forcing 30 (functab-offset × func-offset-anchor) combos yielded exactly one validated parse: functab at base + pcln-offset, function offsets relative to that blob.

`GO_TEXT_BASE` was then calibrated *without disassembly*: a histogram of Go prologue bytes (`49 3b 66 10`) over `.text` in 1MB buckets (~1s runtime) located the Go-dense region, and the first prologue hit preceded by INT3 padding at `0x61d4300` anchored the base. Cross-check: `0x61d4300 + maxEntryOff` landed exactly at the end of the Go region.

Result: **164,366 functions enumerated in 2.9s, <100MB RAM** — no disassembler needed. A second pclntab (19,312 cgo functions) fell out of the same pass. Targeted objdump (≤3 functions) was used only for spot-checks; one region (`FetchConfigFromAICode`) showed a toolchain codegen anomaly and was flagged open rather than papered over.

### Claude Code CLI (Bun-compiled single file)

**Bun string-table carving.** A text-fraction window scan over the 244MB binary found one contiguous 41MB minified-JS blob at file offsets `0xbd00000–0xe41c000`, both ends pinned by binary search. A single occurrence of the string `chunk-d5as4466` at `0x588df71`, read in ±350-char context, cracked the chunk-manifest entry wire format: `name\0\0<kind:u8>\0\0\x80<u32le>` — 2,133 rows parsed (1,965 kind-`0x1e` chunk entries; 168 rows carry other kind tags — corrected 2026-10-19). Five competing hypotheses for the u32 semantics were tested and killed in writing; the table parsed anyway (likely a runtime registry key, not a data pointer). Subsystem offset map via keyword density: entry/startup `0xbd1019a`, auth/OAuth `0xbf00000–0xc180000`, settings `0xcc80000–0xce00000`, permissions `0xd640000–0xd8c0000`, MCP `0xdb80000–0xdf00000`.

**Key procedural lesson:** `re.findall(rb'[ -~]{6,}')` mined 521,976 string runs in 13s, but `grep -o` truncation kept destroying minified-JS context — the lane switched to `re.finditer` with ±350-char windowed context for every extraction.

### Codex CLI (Rust, stripped)

**Schema-generator subcommands.** The binary documents its own protocol: `codex app-server generate-json-schema --out <dir>` emitted the full schema set covering **102 client→server methods, 10 server→client requests, 82 server→client notifications on 0.155.1** (95/10/75/1 was the stale 0.149.0 capture — corrected 2026-10-19). `codex features list` gave the feature-flag inventory. Config recovery came from the serde `FIELDS: &[&str]` statics (**101/101** `ConfigToml` keys in declaration order — the correct method; the prior 97/101 came from lossy packed-run tokenizing) plus the typed resolved Config embedded in the app-server schema's `ConfigReadResponse.json`. The schema's doc-comments served as a fossil record of intended-but-unshipped methods.

## Control experiments (controls beat claims)

- **`--disable_telemetry` refutation (Antigravity).** A lane claimed it was a real hidden CLI flag, "verified" because `agy --disable_telemetry --help` exited 0. The coordinator ran the control: `agy --bogus-flag-xyz --help` also exits 0 — `--help` short-circuits flag parsing. Strict tests (`agy --disable_telemetry models`, `--disable-telemetry`, `=true`) all exit 2 ("flags provided but not defined"). Verdict: not a frontend flag; a `DisableTelemetry` options-struct field exists in rodata with unverified wiring. Lesson: flag-existence tests must use a real subcommand, never `--help`.
- **The gateway correction (Claude).** `claude gateway` was first written up as an enterprise auth/telemetry gateway; deeper strings work corrected it to a full HTTP server (OAuth token, managed settings, inference proxying with a Bedrock upstream). The wrong first writeup is kept as a kill in the record.
- **The telemetry correction (Codex).** The earlier pass said "no opt-out flag found"; the sharper statement is that OTel is opt-*in* (no opt-out needed) while the always-on analytics pipeline is the thing needing `[analytics] enabled = false`. `OTEL_SDK_DISABLED` has zero hits — the kill-switch operators reach for first silently does nothing here.

## Adjudication process

A coordinator lane sat above the six per-tool lanes. It re-ran every PoC and read every lane deliverable, and it overruled workers on evidence: the one refutation (`--disable_telemetry`) and several precision corrections (line-count vs unique-var counts, exact-offset caveats at `0xbd00000`, version-scoped claims) went in as explicit adjudications. The trial phase then re-ran every PoC and spot-checked the ranked findings with exact commands and output excerpts; every trial is logged with command + outcome + verbatim output in `trials-*.md` at the repo-build root. Failed and partial trials stay in the record, marked as such — `claude mcp list` hangs on live health checks (PARTIAL), and that hang is part of the finding.

**Reconstruction honesty:** the Codex lanes' scratchpads for A, C, D, E were reconstructed post-hoc from the lane deliverables on 2026-10-18. Each carries an honest reconstruction header stating what is reconstructible (commands, offsets, quoted literals) and what is partial (discovery procedure, ordering). No contemporaneous timestamps are invented for those entries.

## Constraints honored by every lane

- Read-only: binaries never modified, zero destructive writes.
- Zero network calls to any API; localhost probes only (`127.0.0.1:5387`, `:4713`, both closed).
- Zero metered-model quota burned — no prompts sent to any model.
- No credential values: the token inspector prints structure/expiry/shapes only; auth.json reads are field-names and modes only; OAuth client secrets are withheld everywhere.

## Hard tool limits (recorded 2026-10-19, reinforcement — do not fight these)

- **`rz-bin -z` silently skips >10MB search intervals** on all three binaries. String claims must rest on `reverify` + yara-python + raw `grep -boa`/`pread`, never on rizin string output alone.
- **goresym is incompatible with the go1.28-20260921-RC02 internal toolchain** (OOM SIGKILLs, then clean "no valid pclntab"). The failure itself corroborates the non-upstream-layout claim; use the hand-rolled pclntab parser instead.
- **Ghidra whole-binary analysis OOMs** on this box (slice-only, never over 5MB). **Frida is dead** (no ptrace; static-pie targets). **radare2 install failed** (release asset 404).
- Whole-binary disassembly/emulation is banned: 2 CPUs, ~2.7GB RAM, 0 swap. Slices only.

## Tool-call inventory (the instruments, not secrets)

- `python3` `re.findall(rb'[ -~]{6,}')` / `re.finditer` string mining with ±350-char context windows; pclntab parser; schema counters and diff scripts (all shipped as PoCs under `pocs/`).
- `dd bs=1 skip=<hex-offset>` byte-anchor reads (e.g. `skip=224435288`, `skip=215173117`, `skip=199521935`).
- `grep -aob` byte-offset pattern search; `grep -F`/`grep -cF` counting; `sed -n` line-range reads.
- Live read-only introspection: `codex --help`, `agy --help`, `claude --help`, `codex app-server generate-json-schema --out`, `codex features list`, `claude doctor`, `codex doctor`, `codex debug models`.
- `sha256sum` target pinning; `stat -c '%a'` credential-file modes; `ls -la`; `find`; `timeout` wrappers; `bash -c '</dev/tcp/127.0.0.1/<port>'` loopback probes; `curl`-style localhost `/healthz` probing (connection refused — no LS running, itself a result).
- `diff -rq` for byte-identical schema-set re-verification (291 files, zero diff).
