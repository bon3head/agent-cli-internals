# 03. The binary ships its own source tree: Bun module-graph records, 4,999 zstd frames, 43.5 MB

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
This is the headline method of the whole Droid run: **the target's complete original
unminified source (app + dependencies, 5,484 modules, 50.5 MB decompressed) was recovered
from the binary itself**, turning a string-carving RE pass into a source-reading one.
Method record saved verbatim: `runs/droid/METHOD-source-tree-recovery.md`.

## WHAT WAS FOUND

The ~150–171M region is a Bun standalone module-graph record store: binary record header +
entry in a path/specifier string pool (3,838 paths) + **one zstd frame per module containing
that module's original source**. Census: 5,519 valid frames binary-wide → 5,484 modules,
50,557,968 B decompressed (manifest: `runs/droid/source/MANIFEST.md`: path, offset,
compressed/decompressed size, sha256 per file). The tree was validated three ways:
5,484/5,484 modules parse (bun transpiler); 40+ sampled modules re-associated to binary
offsets with sha256 match; recovered rubric-builder functions **executed** and generated
sentences found byte-for-byte in the frozen binary - the source→binary loop closed.

## HOW IT WAS FOUND (the wrong turns are the lesson)

1. The region was found by region-accounting and labeled a "protobuf per-module record store".
2. A zstd decompression test failed (libzstd error −72) and the region was closed as "not zstd".
   **Both verdicts were wrong.** The −72 came from passing an oversized `srcSize` (region/window
   instead of exact frame length) - the error indicted the test parameters, not the data.
3. The closure wave re-opened the region and re-derived with a different method:
   - "Protobuf" label failed: only 2/3,838 paths show tag+length adjacency.
   - **Association proof**: the frame at offset 150,008,898 follows the path string
     `src/utils/e2eClock.ts` at 150,008,877 and decompresses to exactly that module's source.
     Structure = header + path + frame, proven by content, not shape.
   - Exact frame sizes decompress cleanly. Full census.
4. Dated errata filed against the original claims in place; originals stand.

## WHAT IT UNLOCKS

Any future Bun-compiled binary is now a candidate for this probe: sweep for dense
`.ts/.tsx/.js` path pools, zstd magic (`28 B5 2F FD`) density per region, and test
header+path+frame on the first record before censusing. **Never let a decompression failure
close a region**: a codec error is a claim about your parameters first - retry with exact
frame boundaries before concluding "not this codec". Association beats shape. And kills by
earlier waves are claims, not facts; the most load-bearing ones deserve one re-derivation
with a different method.

## HOW A DEVELOPER BUILDS ON IT

After recovery, the gate order is **source → frozen bytes → prior docs**: every string-carved
claim is provisional until the source check. In this run the source check re-verified or
corrected 59 of 64 claim clusters, including 18 dated errata (finding 01's flag semantics,
finding 02's off switch, finding 04's judge structure).
