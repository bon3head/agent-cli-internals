#!/usr/bin/env python3
"""Ground-truth verifier for extract_mcp_plane.py (red-green gate).
Exits 0 only if the PoC's JSON output contains every known ground-truth item
derived from byte-level evidence in claude CLI 2.1.287.
"""
import json, sys, pathlib

POC_OUT = pathlib.Path(__file__).parent / "mcp-plane-inventory.json"

GROUND_TRUTH = {
    "first_party_blocked_hosts": [
        "microsoft365.mcp.claude.com",
        "gmail.mcp.claude.com",
        "gcal.mcp.claude.com",
    ],
    "first_party_urls": [
        "https://mcp-proxy.anthropic.com",
        "https://slack.mcp.claude.com/mcp",
        "https://microsoft365.mcp.claude.com/mcp",
    ],
    "third_party_urls": [
        "https://mcp.sentry.dev/mcp",
        "https://mcp.asana.com/sse",
        "https://mcp.box.com",
        "https://mcp.figma.com/mcp",
        "https://mcp.linear.app/sse",
    ],
    "transports": ["stdio", "sse", "http", "streamable-http", "ws", "sdk", "claudeai-proxy"],
    "scopes": ["user", "project", "local", "dynamic", "managed", "enterprise"],
    "settings_keys": ["enabledPlugins", "enabledMcpjsonServers", "disabledMcpjsonServers",
                      "enableAllProjectMcpServers", "deniedMcpServers", "allowedMcpServers",
                      "strictKnownMarketplaces", "blockedMarketplaces"],
    "plugin_sources": ["claude-code-marketplace", "claude-plugins-official", "builtin"],
    "kills_absent": ["recommendedPlugins", "plugin share"],
}

def main():
    if not POC_OUT.exists():
        print(f"FAIL: {POC_OUT} does not exist (PoC has not run)")
        return 1
    inv = json.loads(POC_OUT.read_text())
    fails = []
    blob = json.dumps({k: v for k, v in inv.items() if k != "kills"})
    for section, items in GROUND_TRUTH.items():
        if section == "kills_absent":
            for item in items:
                if item in blob:
                    fails.append(f"kills_absent violated: '{item}' present in substantive output")
                if not any(item in k for k in inv.get("kills", [])):
                    fails.append(f"kills_absent not documented: '{item}' missing from kills list")
            continue
        have = set(inv.get(section, []))
        for item in items:
            if item not in have and item not in blob:
                fails.append(f"{section}: missing '{item}'")
    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print(f"PASS: all {sum(len(v) for k, v in GROUND_TRUTH.items() if k != 'kills_absent')} ground-truth items present; kills hold.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
