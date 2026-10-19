# 09 — pclntab cracked: 164,366 functions enumerated in 2.9s, <100MB RAM

**Trial status:** CONFIRMED. `a6_pclntab_dump.py` re-run exit 0 — exactly the report figures: candidate @ `0x1512750` with nfunc=164366, `GO_TEXT_BASE=0x61d4300` (empirical; header textStart==0), second pclntab nfunc=19312. Full 17/17 trial suite passed on the same binary.

---

## 1. WHAT WAS FOUND

Google-internal go1.28 pclntab layout reverse-engineered (upstream Go layout fails here). Byte-exact spec (CONFIRMED):

- pclntab @ file offset `0x1512750` (start of `.lrodata`), magic `0xfffffff1`.
- 72-byte header: magic, `00 00 01 08` (pad, minLC=1, ptrSize=8), nfunc @+8, nfiles @+16, **u64 @+24 = 0 (textStart absent/zeroed — NOT usable)**, funcnameOff @+32 = `0x48`, cuOff @+40, filetabOff @+48, pctabOff @+56, pclnOff @+64 = `0x1d54070`.
- functab at `base+pclnOff`: entries are `(entryOff u32, funcOff u32)` with **funcOff relative to `base+pclnOff`, not to pclntab base** (upstream assumption fails; brute-forced 30 offset/anchor combos, exactly one validated: `functab=pcln, anchor=pcln`, 5/6 probes incl. mid-table).
- func struct: `entryOff u32 @+0`, `nameOff i32 @+4`; name = C-string at `base+funcnameOff+nameOff`; `_func.entryOff == functab entry` cross-check held (binary-searched spot check).
- **Address calibration:** header textStart=0, so entryOff is relative to an unknown base. Empirical: histogram of Go stack-check prologue bytes `49 3b 66 10` (`cmp rsp,[r14+0x10]`) over `.text` in 1MB buckets (~1s) → Go-dense `[0x61d4000, ~0x9355820]`; first hit `0x61d4300`, preceded by C code + INT3 padding. `functab[0]` (entryOff=0) = `internal/abi.(*RegArgs).Dump` lands exactly at `0x61d4300`; `0x61d4300 + maxEntryOff(0x3181520) = 0x9355820` = end of Go region. `GO_TEXT_BASE = 0x61d4300`. Calibrated without disassembly.
- **Bonus:** second pclntab @ `0xc92e520` — 19,312 cgo/C functions (first = `_cgo_9f5b6fa224a3_Cfunc_mygetpwuid_r`); same layout parses it (separate table, not merged into TSV).

Inventory (from `pocs/a6_functions.tsv`, 164,367 lines incl. header, 17.8MB):
- 164,366 Go functions / 33,437 distinct package paths / 6,734 files. 3,249 unnamed, 3,313 `<nopkg>`.
- **144,864 (88%) under `google3/`** — monorepo build; **57,457 in `google3/third_party/jetski/`** (the product): `language_server` (507 methods on `(*Server)`), `cli/store`, `cli/model`, `cortex`, `code_assist_client` (709 fns), `api_server_pb`. Vendored `google3/third_party/golang/` (grpc 5,588 hits, protobuf, genai, openai_go, charm lipgloss). `codeium_common_pb` confirms Windsurf/Codeium lineage.
- CLI parsing lives in `google3/base/go/flag` (Google's flag pkg), not std `flag`. `main` package: 135 functions.
- Targeted objdump (≤3 functions, bounds from TSV): `main.main` @ `0x92cd600` (2520 insns, arg parsing incl. `--version`); `language_server.(*Server).SendAgentMessage` @ `0x8b68480` (gRPC itab dispatch idiom). `FetchConfigFromAICode` region is an **unexplained codegen anomaly** (non-Go prologues at validated addresses; parser exonerated six ways) — open, not blocking.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A6 (deep tooling), 25-minute time box on an 8GB box. Eureka 21:57–22:00: upstream pclntab parse failed (`NO VALID PCLNTAB FOUND`, textStart=0); magic scan found candidate @0x1512750 with nfunc=164366 but a non-upstream header; brute-force over 30 (functab-offset × funcoff-anchor) combos → exactly one validated. Address calibration via prologue histogram (`49 3b 66 10` over `.text`, 1MB buckets, ~1s) → `GO_TEXT_BASE=0x61d4300`, cross-checked two ways. PoC `pocs/a6_pclntab_dump.py`: `python3 pocs/a6_pclntab_dump.py /home/hatch/.local/bin/agy pocs/a6_functions.tsv` → 2.9s, mmap'd, ~50MB peak RSS. radare2 install failed (GitHub asset 404) — documented, abandoned; no Ghidra (documented OOM).

---

## 3. WHAT IT UNLOCKS

Even though the program is stripped of debug info, we fingerprinted Google's internal compiler layout and listed all 164,366 of its functions with names and addresses — in under three seconds, using less memory than a web page. That inventory is a map of the whole machine: which team owns which subsystem, where the agent runtime lives, where the CLI parsing lives. It turns a black-box binary into an address book you can point a disassembler at.

---

## 4. HOW A DEVELOPER BUILDS ON IT

```bash
python3 pocs/a6_pclntab_dump.py /home/hatch/.local/bin/agy /tmp/a6_out.tsv
# columns: address<TAB>name   (addresses are file VMAs — objdump-ready)
```

- Address formula: `0x61d4300 + entryOff`. Do NOT use `.text` start (`0x61d4000` = C code before the Go region).
- Targeted disassembly: `objdump -d --start-address <addr> --stop-address <addr+size> /home/hatch/.local/bin/agy` (function size = next TSV entry − entry; each dump <2s, no full disassembly needed).
- Same layout parses the cgo pclntab @ `0xc92e520` (19,312 fns) — separate text base if C function names are needed.
- Caution: `FetchConfigFromAICode` region disassembles as non-Go prologues at validated addresses — treat disassembly there with suspicion until the codegen anomaly is resolved.
- Reuse: the brute-force layout discovery (magic `0xfffffff1`, 72-byte header, functab=base+pclnOff, funcOff relative to that blob, textStart=0 → prologue-histogram calibration) applies to other binaries built with this Google-internal go1.28 toolchain.
