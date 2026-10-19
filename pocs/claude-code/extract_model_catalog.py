#!/usr/bin/env python3
"""Extract Anthropic's compiled model catalogs from a Claude Code CLI binary (read-only).

Finds and parses two embedded structures in the Bun-compiled JS bundle:
  1. The signed compiled model-catalog SEED:
     {$schema:"https://downloads.claude.ai/model-catalog/v1/schema.json",...}
     (surfaces: cc, ccd, ccr, chat, cowork; model_selector_config/state)
  2. The richer internal model REGISTRY array:
     [{id:"claude-...",family:...,display_name:...,knowledge_cutoff:...,
       provider_ids:{...},context:...,max_output_tokens:...,pricing:...,
       capabilities:[...],default_effort:...,effort_cost_index:...,
       image_limits:...,advisor_rank:...}, ...]
     followed by aliases:{opus:{...},sonnet:{...},haiku:{...},fable:{...}},
     best:"fable", latest_per_family:{...}

Outputs:
  model-catalog-seed.json   - seed document as JSON
  model-registry.json       - registry array + per-provider aliases as JSON
  model-table.md            - human-readable model table

Usage: python3 extract_model_catalog.py /path/to/binary [outdir]
Tested against: claude 2.1.287 (binary offset 215173117 seed, 199521935 registry).
Read-only: never modifies the binary.
"""
import json, re, sys, os

def read_blob(data, start):
    """Walk bytes from `start`, tracking {} depth with string/escape awareness."""
    i, depth, in_str, esc = start, 0, False, False
    while i < len(data):
        b = data[i]
        if in_str:
            if esc: esc = False
            elif b == 0x5c: esc = True
            elif b == 0x22: in_str = False
        else:
            if b == 0x22: in_str = True
            elif b == 0x7b: depth += 1
            elif b == 0x7d:
                depth -= 1
                if depth == 0: break
        i += 1
    if depth != 0:
        raise ValueError("unbalanced braces from offset %d" % start)
    return data[start:i+1].decode('utf-8', errors='replace')

def js_to_json(blob):
    """Convert a JS object literal (unquoted keys, !0/!1) to strict JSON."""
    out, j, n = [], 0, len(blob)
    while j < n:
        c = blob[j]
        if c == '"':
            k, e = j+1, False
            while k < n:
                if e: e = False
                elif blob[k] == '\\': e = True
                elif blob[k] == '"': break
                k += 1
            out.append(blob[j:k+1]); j = k+1; continue
        if c.isalpha() or c in '_$':
            m = re.match(r'[A-Za-z_$][A-Za-z0-9_$]*', blob[j:])
            w = m.group(0)
            if blob[j+len(w):].lstrip().startswith(':'):
                out.append('"'+w+'"'); j += len(w); continue
        out.append(c); j += 1
    s = ''.join(out)
    s = re.sub(r'(?<![0-9A-Za-z_$])!1(?![0-9A-Za-z_$])', 'true', s)
    s = re.sub(r'(?<![0-9A-Za-z_$])!0(?![0-9A-Za-z_$])', 'false', s)
    return s

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        '~/.local/share/claude/versions/2.1.287')
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(outdir, exist_ok=True)
    data = open(src, 'rb').read()

    # 1. seed
    pat = b'{$schema:"https://downloads.claude.ai/model-catalog/v1/schema.json"'
    hits = [m.start() for m in re.finditer(re.escape(pat), data)]
    assert hits, "seed catalog not found"
    seed = json.loads(js_to_json(read_blob(data, hits[0])))
    with open(os.path.join(outdir, 'model-catalog-seed.json'), 'w') as f:
        json.dump(seed, f, indent=1)
    print("seed: version=%s issued=%s expires=%s key=%s surfaces=%s" % (
        seed['version'], seed['issued_at'], seed['expires_at'],
        seed['key_id'], list(seed['surfaces'].keys())))

    # 2. registry array: starts at '[{id:"claude-'
    first = data.find(b'[{id:"claude-')
    assert first >= 0, "registry array not found"
    i, depth, in_str, esc = first, 0, False, False
    while i < len(data):
        b = data[i]
        if in_str:
            if esc: esc = False
            elif b == 0x5c: esc = True
            elif b == 0x22: in_str = False
        else:
            if b == 0x22: in_str = True
            elif b == 0x5b: depth += 1
            elif b == 0x5d:
                depth -= 1
                if depth == 0: break
        i += 1
    reg = json.loads(js_to_json(data[first:i+1].decode('utf-8', errors='replace')))
    models = [e for e in reg if isinstance(e, dict) and 'id' in e]
    with open(os.path.join(outdir, 'model-registry.json'), 'w') as f:
        json.dump(models, f, indent=1)

    # aliases object follows the array: `...}],aliases:{...}},defaults:{},best:"fable",
    # latest_per_family:{...},alias_migration:{}}`
    ai = data.find(b'aliases:{', i, i+60)
    ablob = None
    if ai >= 0:
        brace = ai + len('aliases:')
        ablob = {'aliases': json.loads(js_to_json(read_blob(data, brace)))}
        tail = data[brace:brace+3000].decode('utf-8', errors='replace')
        m = re.search(r'best:"([a-z]+)"', tail)
        if m: ablob['best'] = m.group(1)
        li = tail.find('latest_per_family:{')
        if li >= 0:
            lb = brace + li + len('latest_per_family:')
            ablob['latest_per_family'] = json.loads(js_to_json(read_blob(data, lb)))
        with open(os.path.join(outdir, 'model-aliases.json'), 'w') as f:
            json.dump(ablob, f, indent=1)
    print("registry: %d models, aliases=%s" % (len(models),
          list(ablob.get('aliases', {}).keys()) if ablob else None))

    # 3. markdown table
    lines = ["# Compiled model table (claude CLI seed)", "",
             "| id | family | display | cutoff | pricing | def_effort | adv_rank | ctx_win | max_out | 3p_nulls |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for e in models:
        p = e.get('provider_ids', {}) or {}
        nulls = [k for k, v in p.items() if v is None]
        ctx = (e.get('context') or {}).get('window')
        mo = e.get('max_output_tokens') or {}
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            e['id'], e.get('family'), e.get('display_name'), e.get('knowledge_cutoff'),
            e.get('pricing'), e.get('default_effort'), e.get('advisor_rank'),
            ctx, mo.get('upper'), ",".join(nulls) if nulls else "-"))
    with open(os.path.join(outdir, 'model-table.md'), 'w') as f:
        f.write("\n".join(lines) + "\n")
    print("wrote model-table.md")

if __name__ == '__main__':
    main()
