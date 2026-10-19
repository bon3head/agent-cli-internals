#!/usr/bin/env python3
"""Claude Code auth-surface auditor (read-only).

Inspects the local machine's Claude Code credential storage layout:
paths that exist, file modes, key NAMES (never values), and env vars that
are SET (never their values). Exits 0 always; prints a checklist.
"""
import json, os, stat, sys

def perm(p):
    try: return oct(stat.S_IMODE(os.lstat(p).st_mode))
    except OSError: return None

def yn(v): return "yes" if v else "no"

home = os.path.expanduser("~")
out = []
out.append("== Claude Code auth-surface audit ==")

# 1. OAuth credential file
cf = os.path.join(home, ".claude", ".credentials.json")
out.append(f"file {cf}: exists={yn(os.path.exists(cf))} mode={perm(cf)}")
if os.path.exists(cf):
    try:
        d = json.load(open(cf))
        out.append(f"  top-level keys: {list(d.keys())}")
        oa = d.get("claudeAiOauth")
        if isinstance(oa, dict):
            shapes = {}
            for k, v in oa.items():
                if isinstance(v, str):
                    shapes[k] = f"str(len~{len(v)})"
                elif isinstance(v, list):
                    shapes[k] = f"list(len={len(v)})"
                else:
                    shapes[k] = type(v).__name__
            out.append(f"  claudeAiOauth field shapes: {shapes}")
    except Exception as e:
        out.append(f"  unreadable: {type(e).__name__}")

# 2. config metadata (no tokens there by design)
cj = os.path.join(home, ".claude.json")
out.append(f"file {cj}: exists={yn(os.path.exists(cj))} mode={perm(cj)}")
if os.path.exists(cj):
    try:
        d = json.load(open(cj))
        out.append(f"  has oauthAccount: {yn('oauthAccount' in d)}")
        oa = d.get("oauthAccount")
        if isinstance(oa, dict):
            out.append(f"  oauthAccount keys: {sorted(oa.keys())}")
    except Exception as e:
        out.append(f"  unreadable: {type(e).__name__}")

# 3. env vars: name only, never value
for var in ["ANTHROPIC_API_KEY","ANTHROPIC_AUTH_TOKEN","ANTHROPIC_BASE_URL",
            "ANTHROPIC_CUSTOM_HEADERS","CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR","CLAUDE_CODE_OAUTH_REFRESH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN_FILE","CLAUDE_CODE_API_KEY_FILE_DESCRIPTOR",
            "CLAUDE_CODE_API_KEY_HELPER_TTL_MS","CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX","CLAUDE_CODE_USE_FOUNDRY",
            "CLAUDE_CODE_USE_ANTHROPIC_AWS","CLAUDE_CODE_USE_ANTHROPIC_GOOGLE_CLOUD",
            "CLAUDE_CODE_USE_MANTLE","CLAUDE_CODE_USE_GATEWAY",
            "CLAUDE_CODE_SKIP_BEDROCK_AUTH","CLAUDE_CODE_SKIP_VERTEX_AUTH",
            "CLAUDE_CODE_SIMPLE","ANTHROPIC_FOUNDRY_RESOURCE",
            "ANTHROPIC_VERTEX_PROJECT_ID","GOOGLE_APPLICATION_CREDENTIALS",
            "AWS_PROFILE","AWS_REGION","https_proxy","HTTPS_PROXY"]:
    out.append(f"env {var}: set={yn(var in os.environ)}")

# 4. provider credential files (existence/mode only)
for p in [os.path.join(home,".aws","credentials"),
          os.path.join(home,".aws","config"),
          os.path.join(home,".config","gcloud","application_default_credentials.json")]:
    out.append(f"file {p}: exists={yn(os.path.exists(p))} mode={perm(p)}")

# 5. platform keychain surfaces
import platform
plat = platform.system()
out.append(f"platform: {plat}")
if plat == "Darwin":
    out.append("macOS: OAuth/device keys go to login keychain via `security` CLI (find-generic-password/add-generic-password)")
elif plat == "Windows":
    out.append("Windows: secrets go to Credential Manager")
else:
    out.append("Linux: no OS keychain used; file fallback ~/.claude/.credentials.json is authoritative")

print("\n".join(out))
