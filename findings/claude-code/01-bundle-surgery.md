# 01. Full JS bundle carved from the binary (C6)

**Target pinned:** claude CLI 2.1.287 · Bun-compiled ELF 64-bit x86-64, NOT stripped · 244,317,368 bytes ·
`/home/hatch/.local/share/claude/versions/2.1.287`
**Lane:** C6 (bundle surgery) · **Trial status:** CONFIRMED live (dd re-reads at the carved offsets; the exact-offset
note below records the nuance)
**Confidence:** CONFIRMED (byte-level evidence). The chunk-manifest u32 semantics are INFERENCE/unresolved:
5 hypotheses killed (see §2).

> **Correction (2026-10-19, reinforcement):** the manifest holds **2133 rows**, not 1965 — the prior's
> 1965 was the kind-`0x1e` subset; 168 rows carry other kind tags. JS bounds refined to
> ≈[0xbd0d000, 0xe41d000] (52 KB table header at the claimed start, ~4 KB more JS past the claimed end).

---

## 1. WHAT WAS FOUND

The app is one contiguous **41 MB minified JS blob** at file offsets **0xbd00000–0xe41c000**
(41,009,152 bytes), embedded inside the `.bun` ELF section (file offset 0x54fe000, ~148 MB).
A **2133-row chunk manifest table** at **0x588c868–0x58d8dbc** maps each
`/$bunfs/root/chunk-<hash>.js` name to a u32 (1965 rows are kind-`0x1e` chunk entries; 168 rows
carry other kind tags: see correction note above).

Byte-level evidence:

- Blob bounds found by 1 MB-window text-fraction scan: fraction 1.000 continuously from 0xbe00000 to
  0xe400000; binary→text transition at 0xbd00000, text→binary at ≈0xe41c000 (binary-searched to 4 KB).
  After a ~0.3–1 KB binary header (`0xbd00000–0xbd00300`), the region is one uninterrupted minified
  JS bundle (`import"/$bunfs/root/chunk-*.js"` cross-chunk imports throughout). The blob tail
  (last KBs) is an import manifest:
  `import"/$bunfs/root/chunk-d5as4466.js";import"/$bunfs/root/chunk-arb5mqam.js";…`
- Manifest entry wire format (decoded, byte-verified for all 2133 rows):
  `[name bytes][0x00][0x00][kind:u8][0x00][0x00][0x80][value:u32 LE]`, with `kind=0x1e` for chunk
  entries (name length 30, e.g. `/$bunfs/root/chunk-w5read84.js`). The same wire format is reused
  for node-builtin shims (`child_process`→`spawn`, `fs/promises`→`access`/`stat`/`open`) and an
  FFI type table (`Cwchar_t`, `Cwstring`, `DenseArray`, ~0x5ae36d4); `kind` is a type tag (values
  0x02–0x2d observed), not a length.
- Carved, byte-exact, in `~/workspace/rea-claude/deep-dive/carved/`:
  `claude-bundle-full.js` (41 MB, the full blob), `chunk-manifest.json` (2133 rows: name,
  table offset, u32 value), `01-settings.js` (1.5 MB, 0xcc80000–0xce00000),
  `02-auth-oauth.js` (2.5 MB, 0xbf00000–0xc180000), `03-mcp-protocol.js` (3.5 MB, 0xdb80000–0xdf00000).
  Each slice carries a header comment with source offsets + decode method. Slices are minified
  excerpts, not standalone-runnable.
- Subsystem offset map (blob-relative file offsets, keyword-density histograms, CONFIRMED by
  direct read): entry/startup 0xbd1019a (`process.env.NoDefaultCurrentDirectoryInExePath="1"`),
  auth/OAuth 0xbf00000–0xc180000, settings 0xcc80000–0xce00000, permissions engine
  0xd640000–0xd8c0000, MCP 0xdb80000–0xdf00000.
- Trial nuance: at exactly 0xbd00000 the first ~200 B are the **binary header**, not JS;
  JS text is confirmed from ~0xbd10000 onward, and 4096/4096 printable bytes at 0xc000000.
  The manifest-entry crack example reads `...chunk-w5read84.js\x00\x00\x1e\x00\x00\x80\xcb\xde>\x00/...`.

## 2. HOW IT WAS FOUND

- Lane C6: read-only python `open(...,'rb')` + `struct`/regex; no disassembler, binary never
  modified, zero model quota. Scratchpad: `scratchpad-c6.md`.
- **21:55–22:0x:** text-fraction window scan locates the 41 MB bundle blob (0xbd00000–0xe41c000);
  binary search pins both ends to 4 KB.
- The single `chunk-d5as4466` occurrence at **0x588df71** in context
  `...chunk-w5read84.js\x00\x00\x1e\x00\x00\x80\xcb\xde>\x00/...` cracks the manifest entry
  pattern; regex `rb'/\$bunfs/root/chunk-([a-z0-9]+)\.js\x00\x00\x1e\x00\x00\x80(....)'` parses
  all 2133 rows.
- Non-text cluster analysis: 45,933 non-text bytes in the blob; all ≥4-byte clusters live in the
  header → the "length-prefixed string table" hypothesis is **dead**; there are no length-prefix
  separators between modules.
- **Killed (documented):** chunk-manifest u32 semantics: 5 hypotheses dead: (1) u32 as
  length-prefix walk, (2) u32 as sizes concatenated in table order (sums to 16.4 GB >> 244 MB),
  (3) u32 as offset into blob from 0xbd00000 (boundaries land mid-token), (4) u32 as offset
  from `.bun` section start, (5) u32 as offset of the chunk's own name string.
  INFERENCE: the u32 is likely a runtime registry key (module slot / intern id), not a file
  data pointer.
- Trial re-run (`trials-claude-code.md`, 2026-10-18): dd re-reads at 0xbd10000/0xbd80000/0xbe00000/
  0xc000000/0xd800000 on the live binary → CONFIRMED.

## 3. WHAT IT UNLOCKS

In plain terms: the CLI is no longer a black box. Its entire program (settings handling, auth
flows, the MCP client, the permission engine, the model catalog) is now readable JavaScript
sitting on disk. Every future question about this exact build ("does it read X?", "what does
this flag actually do?") is answerable by grepping a file, without re-extracting anything or
burning any model quota. It is the foundation every other finding in this set stands on.

## 4. HOW A DEVELOPER BUILDS ON IT

- Grep the bundle for any behavior question: e.g. subsystem search: `grep -aob "some_flag"
  carved/claude-bundle-full.js` gives a byte offset; `dd bs=1 skip=<off-500> count=2000` shows
  the minified context. This exact recipe was used for every other finding doc.
- Subsystem slices: read `01-settings.js` (0xcc80000–0xce00000), `02-auth-oauth.js`
  (0xbf00000–0xc180000), `03-mcp-protocol.js` (0xdb80000–0xdf00000) instead of the full 41 MB
  when the subsystem is known: see `~/workspace/rea-claude/deep-dive/carved/`.
- Manifest: `chunk-manifest.json` (2133 rows with table offset + u32 value) is the index for
  any chunk-name→location lookup. Re-carve by parsing the table, not by re-scanning the binary.
- Caveats for reuse: offsets are version-pinned to 2.1.287; re-run the text-fraction scan on a
  new build rather than hard-coding them; carved slices are excerpts, not runnable JS.
