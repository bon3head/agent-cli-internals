# Finding 12 — The code-mode sandbox is exactly 14 injected names (and no more)

**Version pin:** host binary `codex-code-mode-host` 0.155.1, 69,423,168 bytes,
sha256 prefix `210ab8ebaebf4bc1421d9e30339c8583` (ships in the same vendor dir
as codex CLI 0.155.1, sha256 `0753dfe1…b761`). All offsets are file offsets in
the host image.

## 1. WHAT WAS FOUND

The JavaScript cells that code mode executes do **not** run in a generic JS
environment. The host injects exactly 14 names into each cell and nothing else
beyond native V8 builtins (Promise/Math/JSON) and per-subscribed-tool functions.
The full set, in binary order:

```
console, Atomics, SharedArrayBuffer, WebAssembly, clearTimeout, setTimeout,
image, audio, generatedImage, store, notify, yield_control, tools, ALL_TOOLS
```

Evidence (host binary, file offset 46281610 — re-verified on this pass by
dumping the bytes immediately after the `failed to allocate helper name` format
string): the 14 names sit back-to-back with no separators, in exactly this
order:

```
failed to allocate helper name|console|Atomics|SharedArrayBuffer|WebAssembly|
clearTimeout|setTimeout|image|audio|generatedImage|store|notify|yield_control|
tools|ALL_TOOLS|failed to allocate tool name...
```

(Adjacent: `failed to append ALL_TOOLS metadata`, `failed to set ALL_TOOLS
description/name` — the host builds an `ALL_TOOLS` metadata object with
name/description per subscribed tool.)

Explicitly **absent** (zero whole-token occurrences in the cell-actor string
pool region 0x2c22000–0x2c24000, re-verified by raw byte scan on this pass):

```
setInterval: 0 | process: 0 | Buffer: 0 (the one hit is inside SharedArrayBuffer)
module: 0 | exports: 0 | queueMicrotask: 0
```

`fetch` is not a cell global either: the only `fetch` occurrence in the region
sits inside an HTTP header-name list (`upgrade-insecure-requests`, `warning`,
`x-content-type-options` — a reqwest header pool @0x2c1b7be), not a registered
helper name.

What the sandbox permits vs forbids:

| Permitted | Evidence |
|---|---|
| `console` (logging) | injected name #1; routing target UNRECOVERED |
| `Atomics`, `SharedArrayBuffer`, `WebAssembly` | injected names #2–4 |
| `setTimeout` / `clearTimeout` timers | `setTimeout expects a function callback`, `clearTimeout expects a numeric timeout id` @0x2c23006, in `code-mode-runtime/src/cell_actor/callbacks.rs:35,110` |
| `image` / `audio` / `generatedImage` content constructors | `image` keys `image_url`, `detail` (`image detail must be a string when provided`); `audio` key `audio_url`; `generatedImage` key `output_hint`; `*image only accepts MCP image blocks, got " "` @0x2b2d85e |
| `store` (serializable-only KV) | `store key must be a string`; `Unable to store {key}. Only plain serializable objects can be stored.` @0x2b2d8c4 |
| `notify` (text → host notification) | `notify expects non-empty text` (→ `notification/send`) |
| `yield_control` (cooperative yield hook) | single occurrence @0x2c2340b; semantics UNRECOVERED beyond the name |
| `tools` object + `ALL_TOOLS` metadata | per-subscribed-tool promise-returning functions (allow-listed; JS calling an unsubscribed tool gets `unknown tool call \` \`` @0x2b2d792) |

| Forbidden | Evidence |
|---|---|
| `fetch` / any network API | no global; cell is deliberately network-blind |
| `setInterval` | no global — only one-shot timers; no recurring loops |
| `process`, `Buffer`, `require`, `module`, `exports` | no Node surface at all |
| `queueMicrotask` | no global |
| `import` statements | `Unsupported import in exec: ` @0x2b2d701 — cells compile as classic scripts, not modules |

Consequence: a cell cannot phone home, cannot spawn recurring work, cannot touch
Node APIs. It computes, builds content blocks (text/image/audio), persists
serializable values, pokes the host via `notify`, yields cooperatively, and calls
only the tools the main process explicitly subscribed. The cell's network
surface is exactly the tool-invocation delegation channel (`code_mode.runtime.invoke_tool`
span; invocation IDs must be UUIDs and unique — `code-mode tool invocation ID
must be a UUID`, `code-mode tool invocation ID was reused`).

HYPOTHESIS (mechanism unconfirmed): the `--jitless` literal sits in the
cell-actor string pool @0x2c22ad9 between `generatedImage expects an image
generation result object` and rusty_v8 runtime-init strings — V8 likely runs
jitless, but no call-site (`set_flags_from_string`) was recovered, so this is
placement evidence only. UNVERIFIED.

**Dated note:** prior docs said "thin sandbox" without enumerating the surface.
This finding replaces that with the enumerated 14-name set + negatives, both
against 0.155.1 (not the stale 0.149.0 baseline).

## 2. HOW IT WAS FOUND (exact tool, command, offset — reproducible)

Tool: raw byte scan + `strings -n 8`; no disassembly, no network.

Reproduction (this pass, independent of the original lane):

```python
import re
h = open('codex-code-mode-host-0.155.1','rb').read()
i = h.find(b'failed to allocate helper name')   # file offset 46281610
seg = h[i:i+200]
print(repr(seg))
# -> b'failed to allocate helper name\x00console\x00Atomics\x00SharedArrayBuffer\x00
#      WebAssembly\x00clearTimeout\x00setTimeout\x00image\x00audio\x00generatedImage\x00
#      store\x00notify\x00yield_control\x00tools\x00ALL_TOOLS\x00...'
```

Negatives (raw token counts in the cell-actor pool region 0x2c22000–0x2c24000,
vaddr == file offset, base-0 static-pie):

```python
pool = h[46260224:46268416]
for t in [b'setInterval', b'process', b'Buffer', b'module', b'exports', b'queueMicrotask']:
    assert len(re.findall(t, pool)) == 0
```

Cross-refs from the strings dump: the helper-registration errors live in
`code-mode-runtime/src/cell_actor/callbacks.rs` (path literal @0x2c23006);
the tool-binding spans at `code_mode.runtime.invoke_tool` @0x2c2330a region
(`failed to create tool function`, `failed to allocate tool callback data`,
`failed to create tool promise`); `struct WireNestedToolCall with 5 elements`:
`cell_id, runtime_tool_call_id, tool_name, tool_kind, input` (codex binary
@0xd24d203).

## 3. WHAT IT UNLOCKS (plain language, no jargon)

Think of a code-mode cell as a calculator in a glass box. The calculator can do
math, draw pictures, save notes on an index card, ring a bell to get the host's
attention, and hand the host a work order for one of the approved tools. It
cannot open a web page, cannot set a repeating alarm, cannot run forever, and
cannot load outside code. That is the entire security story in one sentence:
the sandbox's power is precisely 14 words long, and everything else is locked
out. Knowing the exact list means you know exactly what agent code can and
cannot reach — no guessing whether `fetch` is hiding somewhere (it isn't).

## 4. HOW A DEVELOPER BUILDS ON IT (concrete, cut-and-dry)

1. Writing cell code? Target only these 14 names + Promise/Math/JSON + the
   subscribed tool functions. Anything else (`setInterval`, `fetch`,
   `process`, `Buffer`, `import`, `queueMicrotask`) fails — don't rely on it.
2. Need recurring work in a cell? You can't — use `setTimeout` chains or
   `yield_control` loops instead; `setTimeout expects a function callback` and
   `clearTimeout expects a numeric timeout id` are the only timer APIs.
3. Persisting state between cells: `store` accepts only plain serializable
   objects — no class instances, no functions, no circular refs
   (`Unable to store {key}. Only plain serializable objects can be stored.`).
4. Tool invocation from a cell: call the injected per-tool function; each call
   carries a UUID invocation ID, and IDs must be unique (`code-mode tool
   invocation ID was reused` → error). Generate v4 UUIDs client-side.
5. Content returns: build them with `image({image_url, detail?})`,
   `audio({audio_url})`, `generatedImage({output_hint})`; results fed back into
   JS accept only MCP blocks — binary data must be a `data: ;base64,` data URI
   (`Pass a base64 data URI instead`).
