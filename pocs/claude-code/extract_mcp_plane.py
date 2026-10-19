#!/usr/bin/env python3
"""extract_mcp_plane.py — MCP & plugin control-plane inventory extractor.

Reads the Claude Code CLI binary READ-ONLY (no network, no model calls) and
emits a structured reference of the MCP and plugin planes:
  - mcp-plane-inventory.json  (machine-readable)
  - mcp-plane-inventory.md    (human-readable)

Usage: python3 extract_mcp_plane.py [binary_path]
Default binary: /home/hatch/.local/share/claude/versions/2.1.287
"""
import json, re, sys, pathlib
from datetime import datetime, timezone

BIN = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else
                    "/home/hatch/.local/share/claude/versions/2.1.287")
OUT = pathlib.Path(__file__).parent

SETTINGS_KEYS = [
    "enabledPlugins", "plugin_marketplaces",
    "enabledMcpjsonServers", "disabledMcpjsonServers", "enableAllProjectMcpServers",
    "strictMcpConfig", "allowedMcpServers", "deniedMcpServers",
    "allowManagedMcpServersOnly", "blockedMarketplaces", "strictKnownMarketplaces",
    "allowedProviders", "tengu_mcp_local_oauth_blocked_hosts",
]

TRANSPORTS = ["stdio", "sse", "http", "streamable-http", "ws", "sdk",
              "claudeai-proxy", "sse-ide", "ws-ide"]

SCOPES = ["user", "project", "local", "dynamic", "managed", "enterprise"]

PLUGIN_SOURCES = ["claude-code-marketplace", "claude-plugins-official", "builtin",
                  "skills-dir", "claudeai"]

BLOCKED_HOSTS_RE = re.compile(
    rb'\["(?:[a-z0-9-]+\.)*mcp\.claude\.com"(?:,"(?:[a-z0-9-]+\.)*mcp\.claude\.com")+\]')


def main():
    data = BIN.read_bytes()
    inv = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "binary": str(BIN),
        "binary_bytes": len(data),
        "first_party_blocked_hosts": [],
        "first_party_urls": [],
        "third_party_urls": [],
        "transports": [],
        "scopes": [],
        "settings_keys": {},
        "plugin_sources": [],
        "marketplace_sources": [],
        "plugin_manifest_fields": [],
        "permission_rule_evidence": [],
        "kills": [],
    }

    # 1. First-party blocked-host arrays: ["microsoft365.mcp.claude.com","gmail...","gcal..."]
    seen = set()
    for m in BLOCKED_HOSTS_RE.finditer(data):
        hosts = re.findall(rb'"([a-z0-9-]+\.mcp\.claude\.com)"', m.group(0))
        for h in hosts:
            hs = h.decode()
            if hs not in seen:
                seen.add(hs)
                inv["first_party_blocked_hosts"].append(hs)

    # 2. All MCP-ish endpoint URLs
    url_re = re.compile(rb'https?://[A-Za-z0-9_.-]*mcp[A-Za-z0-9_./-]*')
    urls = sorted({m.group(0).decode(errors="replace") for m in url_re.finditer(data)})
    for u in urls:
        (inv["first_party_urls"] if ".claude.com" in u or "anthropic.com" in u
         else inv["third_party_urls"]).append(u)

    # 3. Transports / scopes: require quoted token presence in binary
    for t in TRANSPORTS:
        if re.search(rb'["\']' + t.encode() + rb'["\']', data):
            inv["transports"].append(t)
    scope_re = re.compile(rb'config scope \(`user`, `project`, `local`, `dynamic`')
    scope_doc_found = bool(scope_re.search(data))
    for s in SCOPES:
        if re.search(rb'["\']' + s.encode() + rb'["\']', data):
            inv["scopes"].append(s)

    # 4. Settings keys with occurrence counts
    for k in SETTINGS_KEYS:
        n = len(re.findall(re.escape(k).encode(), data))
        if n:
            inv["settings_keys"][k] = n

    # 5. Plugin sources / marketplace protocol markers
    for s in PLUGIN_SOURCES:
        if s.encode() in data:
            inv["plugin_sources"].append(s)
    for marker, label in [
        (b"plugin_marketplaces", "plugin_marketplaces settings key (git repo default)"),
        (b"marketplace GCS failed; falling back to git", "GCS primary fetch, git fallback"),
        (b"@acme/claude-marketplace", "marketplace as npm package"),
        (b"manifestSha256", "manifestSha256 trust pin"),
        (b"installationPreference", "installationPreference: available|required|auto_install|not_available"),
        (b"headersHelper", "headersHelper runtime header command"),
        (b".mcpb", "MCPB bundled server bundle"),
        (b".dxt", "DXT (Desktop Extension) bundle"),
    ]:
        if marker in data:
            inv["marketplace_sources"].append(label)

    # 6. Plugin manifest fields via manifest.<field> references
    fields = sorted({m.group(1).decode() for m in
                     re.finditer(rb'manifest\.([a-zA-Z]+)', data)})
    inv["plugin_manifest_fields"] = [f for f in fields
                                     if f in {"name", "version", "description", "author",
                                              "license", "homepage", "repository", "keywords",
                                              "userConfig", "hooks", "mcpServers", "lspServers",
                                              "outputStyles", "channels", "monitors",
                                              "workflows", "strict"}]

    # 7. Permission-rule evidence quotes (byte-exact, truncated)
    for pat in [rb'globs are permitted only in the tool position.{0,80}',
                rb"Use 'mcp__<server>' to deny one server's tools",
                rb'--allowedTools \\"mcp__']:
        for m in re.finditer(pat, data):
            q = m.group(0).decode(errors="replace")
            if q not in inv["permission_rule_evidence"]:
                inv["permission_rule_evidence"].append(q)

    # 8. Documented kills (expected-absent)
    for marker, note in [("recommendedPlugins", "settings key absent in 2.1.287"),
                         ("sharePlugin", "no plugin-share surface"),
                         ("pluginShare", "no plugin-share surface"),
                         ("plugin share", "no plugin-share surface (checked case-insensitive, 0 hits)")]:
        if marker.replace(" ", "").lower().encode() not in data.lower().replace(b" ", b""):
            inv["kills"].append(f"{marker}: absent — {note}")

    # Write JSON
    (OUT / "mcp-plane-inventory.json").write_text(json.dumps(inv, indent=2))

    # Write Markdown
    lines = ["# MCP & Plugin Control-Plane Inventory",
             f"_Extracted {inv['generated_utc']} from `{BIN}` ({len(data)} bytes), read-only, zero network._",
             "",
             "## First-party endpoints",
             "",
             "### Anthropic-hosted OAuth-blocked hosts (`tengu_mcp_local_oauth_blocked_hosts`)"]
    for h in inv["first_party_blocked_hosts"]:
        lines.append(f"- `{h}`")
    lines += ["", "### First-party URLs found in binary", ""]
    for u in inv["first_party_urls"]:
        lines.append(f"- `{u}`")
    lines += ["", "### Third-party MCP URLs found in binary", ""]
    for u in inv["third_party_urls"]:
        lines.append(f"- `{u}`")
    lines += ["", "## Transports", ""]
    lines.append(", ".join(f"`{t}`" for t in inv["transports"]))
    lines += ["", "## Config scopes", ""]
    lines.append(", ".join(f"`{s}`" for s in inv["scopes"]))
    lines += ["", "## Settings keys (with occurrence counts)", ""]
    for k, n in sorted(inv["settings_keys"].items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{k}` x{n}")
    lines += ["", "## Plugin sources", ""]
    for s in inv["plugin_sources"]:
        lines.append(f"- `{s}`")
    lines += ["", "## Marketplace protocol markers", ""]
    for s in inv["marketplace_sources"]:
        lines.append(f"- {s}")
    lines += ["", "## Plugin manifest fields (`manifest.<field>` references)", ""]
    lines.append(", ".join(f"`{f}`" for f in inv["plugin_manifest_fields"]))
    lines += ["", "## Permission-rule evidence (byte-exact quotes)", ""]
    for q in inv["permission_rule_evidence"]:
        lines.append(f"> {q}")
    lines += ["", "## Kills (verified absent)", ""]
    for k in inv["kills"]:
        lines.append(f"- {k}")
    (OUT / "mcp-plane-inventory.md").write_text("\n".join(lines) + "\n")

    print(f"wrote {OUT/'mcp-plane-inventory.json'} and {OUT/'mcp-plane-inventory.md'}")
    print(f"first-party blocked hosts: {inv['first_party_blocked_hosts']}")
    print(f"first-party urls: {len(inv['first_party_urls'])}, third-party urls: {len(inv['third_party_urls'])}")


if __name__ == "__main__":
    main()
