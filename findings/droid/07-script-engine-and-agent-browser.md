# 07. The script engine, the agent browser, and the internal QA skill everyone got

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Gate-checked against the recovered source.

## WHAT WAS FOUND

**A bespoke sandboxed script engine**: a 58,933,305 B ELF (19.95% of the file) at offset
206,591,954 - Rust + the V8 crate (v150.4.0), *not* Deno/Node/Electron. JSON frame protocol
(`Frame::Evaluate` / `ToolResult`, `__mission_record__`, `__script_host`, 10 MiB frames,
an "Unsafe Script tool binding" class). It backs the agent-visible `Script` tool
([prompts/droid.md §5.4](../../prompts/droid.md#54-the-script-tool-script-only-execution-mode)).

**`fff`**: the mystery 25.6 MB ELF is a Rust fast-file-finder backed by LMDB (90 `fff_*`
dynsyms). The `@201,453,026` "ripgrep ELF" was a false positive (dated erratum filed).

**`agent-browser`**: true extent 14,251,979 B (the earlier 28.5 MB was a segment-map
artifact - dated erratum). Bundled with the **`dogfood` skill** (skill asset @282223838):
Factory's internal "systematically explore a web app" QA workflow, shipped to every user,
driving the browser binary.

Two undocumented builtin mission skills: **`refactoring-playbook`** (characterization
testing, strangler fig, incremental migration) and **`tui-application-playbook`** (vertical
slices, walking skeleton, tuistory verification) - `src/skills/builtin/constants.ts:2516,2721`
(wave-3 addendum in the prompt corpus). The software-factory worker prompts (Factory's
internal QA loop workstream DB, `packages/software-factory-db/src`) were **not** recovered:
only endpoints and the reproduction-first bug-fix gate are characterized - carried as an
honest residual.

## HOW IT WAS FOUND / WHAT IT UNLOCKS

BRUTE ULTRA MAX (engine ELF identification, `fff` dynsym census), closure wave
(agent-browser extent correction, dogfood skill text). A script-execution sandbox with a
"Unsafe Script" binding shipped inside a coding CLI is a surface worth its own threat
model; the shipped internal-QA skill is the sharpest evidence that the vendor dogfoods
the binary you run.
