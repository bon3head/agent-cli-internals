#!/usr/bin/env python3
"""cloud_mapper.py — read-only static mapper for the Claude Code CLI cloud+gateway control planes.

Extracts printable runs from the Bun-compiled binary (or a pre-extracted
strings file) and organizes every cloud/gateway endpoint, CLI flag, env var,
session-id pattern, config key and host into a markdown reference table + JSON.

Usage:
    python3 cloud_mapper.py /path/to/claude-binary [--strings /tmp/strings.txt]
                        [--out-dir ./cloud-map]

Zero network. Zero model quota. Read-only.
"""
import json
import re
import sys
import argparse
from pathlib import Path

MIN_RUN = 6

FLAG_RE = re.compile(
    r"--(?:cloud|environment|teleport|watch-artifact(?:-no-autoreact)?|await-claim|"
    r"client-data-url|attach-serve|remote|ref|on-branch|correlation-id|session-id|"
    r"file|project|pool|init-only|sdk-url)(?![A-Za-z0-9_-])"
)
ENDPOINT_RE = re.compile(
    r'["\'`](/(?:v1|v2)/code[A-Za-z0-9/_.$:{}\-]*)["\'`]'
)
API_RE = re.compile(
    r'["\'`](/(?:api|oauth|managed|user)[A-Za-z0-9/_.$:{}\-]*)["\'`]'
)
ENV_RE = re.compile(
    r"\b(CLAUDE_CODE_(?:USE_GATEWAY|CLIENT_DATA_URL|ULTRAREVIEW_[A-Z_]+|"
    r"REMOTE_CONTROL_[A-Z_]+|SESSION_[A-Z_]+|SUBPROCESS_[A-Z_]+)|"
    r"SELF_HOSTED_RUNNER_(?:POOL_SECRET|ENVIRONMENT_SECRET)|"
    r"ANTHROPIC_(?:BASE_URL|AUTH_TOKEN|API_KEY))\b"
)
IDPREFIX_RE = re.compile(r"\b(session_|cse_|ccpool_)[A-Za-z0-9_.\-]*")
GATEWAY_KEY_RE = re.compile(
    r"\b(forceLoginGatewayUrl|forceLoginMethod|forceLoginOrgUUID|"
    r"gatewayInternalNetworks|serve_to_desktop|allowedProviders)\b"
)
HOST_RE = re.compile(
    r'https?://(?:[a-z0-9\-]+\.)?(?:claude\.ai|anthropic\.com|'
    r'claudeusercontent\.com|platform\.claude\.com|code\.claude\.com)'
    r'(?:/[A-Za-z0-9/_.$:{}\-?=&%]*)?'
)
SESSION_ID_FMT_RE = re.compile(r"\^\(\?:session\|cse\)_[^$]+\$")


def extract_runs(path: Path):
    data = path.read_bytes()
    return re.findall(rb"[ -~]{%d,}" % MIN_RUN, data)


def load_corpus(binary: Path, strings_file: Path | None):
    if strings_file and strings_file.exists():
        raw = strings_file.read_bytes().split(b"\n")
    else:
        raw = extract_runs(binary)
    # join to one text; keep line boundaries so greps stay honest
    return b"\n".join(raw).decode("utf-8", errors="replace")


def collect(pattern, text):
    hits = {}
    for m in pattern.finditer(text):
        v = m.group(1) if m.lastindex else m.group(0)
        hits[v] = hits.get(v, 0) + 1
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("binary", help="claude CLI binary (read-only)")
    ap.add_argument("--strings", default=None,
                    help="pre-extracted strings file (skips binary scan)")
    ap.add_argument("--out-dir", default="cloud-map",
                    help="output directory")
    args = ap.parse_args()

    binary = Path(args.binary)
    assert binary.exists(), f"binary not found: {binary}"
    text = load_corpus(binary, Path(args.strings) if args.strings else None)
    assert len(text) > 1_000_000, "corpus suspiciously small — wrong input?"

    tables = {
        "endpoints": collect(ENDPOINT_RE, text),
        "api_paths": collect(API_RE, text),
        "flags": collect(FLAG_RE, text),
        "env_vars": collect(ENV_RE, text),
        "id_prefixes": collect(IDPREFIX_RE, text),
        "gateway_keys": collect(GATEWAY_KEY_RE, text),
        "hosts": collect(HOST_RE, text),
        "session_id_formats": collect(SESSION_ID_FMT_RE, text),
    }

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "cloud-map.json").write_text(
        json.dumps(tables, indent=1, sort_keys=True))
    lines = ["# Claude Code CLI cloud+gateway reference (static extraction)",
             "",
             f"Source: `{binary}` — printable-run scan, no execution, no network.",
             ""]
    titles = {
        "endpoints": "Cloud session / runner / bridge endpoints",
        "api_paths": "OAuth / settings / misc API paths",
        "flags": "Cloud-related CLI flags",
        "env_vars": "Cloud/gateway env vars",
        "id_prefixes": "Session / environment id prefixes",
        "gateway_keys": "Gateway config / policy keys",
        "hosts": "First-party hosts",
        "session_id_formats": "Session id regexes",
    }
    for key, title in titles.items():
        items = tables[key]
        lines += [f"## {title} ({len(items)})", "",
                  "| value | hits |", "|---|---|"]
        for v, n in sorted(items.items(), key=lambda kv: (-kv[1], kv[0])):
            v = v.replace("|", "\\|")
            lines.append(f"| `{v}` | {n} |")
        lines.append("")
    (out / "cloud-map.md").write_text("\n".join(lines))
    total = sum(len(v) for v in tables.values())
    print(f"wrote {out/'cloud-map.md'} and {out/'cloud-map.json'}")
    print(f"{total} distinct values across {len(tables)} tables")
    for key in titles:
        print(f"  {key}: {len(tables[key])}")


if __name__ == "__main__":
    main()
