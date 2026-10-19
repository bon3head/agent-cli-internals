#!/usr/bin/env python3
"""A1 lane: enumerate every server/IPC/control surface in the agy binary.
Read-only: runs `strings` on the given binary path and extracts the inventory.
Usage: python3 a1_enumerate_surfaces.py /home/hatch/.local/bin/agy
"""
import re, subprocess, sys, hashlib

PATH = sys.argv[1] if len(sys.argv) > 1 else "/home/hatch/.local/bin/agy"

h = hashlib.sha256(open(PATH, "rb").read()).hexdigest()
print(f"# target: {PATH}\n# sha256: {h}\n")
S = subprocess.run(["strings", "-a", "-n", "4", PATH], capture_output=True).stdout

def lines_of(blob, marker, n=2, width=160):
    for m in list(re.finditer(re.escape(marker), blob))[:n]:
        a, b = max(0, m.start()-width), m.start()+width
        yield m.start(), blob[a:b].replace(b"\n", b" | ")[:width*2]

# --- 1. gRPC method paths -----------------------------------------------------
SERVICES = {
    "exa.language_server_pb.LanguageServerService": rb"exa\.language_server_pb\.LanguageServerService",
    "exa.api_server_pb.ApiServerService": rb"exa\.api_server_pb\.ApiServerService",
    "devtools_jetski_boq_api_proto.ApiService": rb"devtools_jetski_boq_api_proto\.ApiService",
}
# junk suffixes observed from strings-adjacency (descriptor bytes / next string)
JUNK = re.compile(
    r"(failed|Failed|Cannot|cannot|Skipping|Ignoring|unsupported|Markdown|builtin|"
    r"https|trace|crypto|cryptobyte|genai|config|stripped|The|tls|certificate|ssh|"
    r"project_id|resolveFileIncludes|compositeCustomization|Count|"
    r"CONVERSATION_GROUP_SORT_MODE_(LAST_USER_PROMPT|UNSPECIFIED)|"
    r"Z[B-J]|b[0-9a-f]{16,}.*)$"
)
for svc, pat in SERVICES.items():
    meths = {}
    for m in re.finditer(pat + rb"/([A-Za-z][A-Za-z0-9_]*)", S):
        name, off = m.group(1).decode(), m.start()
        clean = JUNK.sub("", name)
        meths.setdefault(clean, []).append((off, clean != name))
    real = {k: v for k, v in meths.items() if any(not f for _, f in v)}
    always_sus = {k: v for k, v in meths.items() if all(f for _, f in v)}
    print(f"## {svc}: {len(real)} methods ({len(always_sus)} only-ever-suspicious forms)")
    for k in sorted(real):
        offs = ",".join(str(o) for o, f in real[k][:3] if not f) or \
               ",".join(str(o) for o, _ in real[k][:3])
        print(f"  {k}  @{offs}")
    if always_sus:
        print("  --- only seen in concat-artifact form (verify before trusting):")
        for k in sorted(always_sus):
            print(f"    {k}  @{always_sus[k][0][0]}")
    print()

# --- 2. ANTIGRAVITY_* env vars ------------------------------------------------
envs = sorted(set(re.findall(rb"ANTIGRAVITY_[A-Z][A-Z0-9_]*", S)))
# A long hit that CONTAINS a shorter distinct hit (or is >45 chars of CAPS soup)
# is a strings-adjacency artifact; the short hits are the real vars.
short = {e for e in envs if len(e) <= 45}
artifacts = [e for e in envs
             if len(e) > 45 and any(o != e and o in e for o in short)]
real = [e for e in envs if e not in artifacts]
print(f"## ANTIGRAVITY_* env vars ({len(real)} real, {len(artifacts)} concat artifacts)")
for e in real:
    print(f"  {e.decode()}")
if artifacts:
    print("  --- concat artifacts (ignore):")
    for e in artifacts:
        print(f"    {e.decode()[:120]}")
print()

# --- 3. listeners / sockets / endpoints ---------------------------------------
print("## listener & socket indicators")
for label, pat in [
    ("loopback ports", rb"(?:localhost|127\.0\.0\.1):[0-9]{2,5}"),
    ("unix socks", rb"(?:/run/user/%d|[\w/.-]*\.sock)"),
    ("health probes", rb"/health[a-z]*"),
    ("grpc handlers", rb"connect\.New\w*Handler"),
    ("net.Listen sites", rb"net\.Listen"),
]:
    hits = set(re.findall(pat, S))
    print(f"  {label}: {len(hits)} distinct")
    for x in sorted(hits)[:25]:
        print(f"    {x.decode(errors='replace')}")
print()

print("## evidence samples")
for marker in [b'ANTIGRAVITY_LS_ADDRESS:=localhost:5387',
               b'http://${ANTIGRAVITY_LS_ADDRESS}/healthz',
               b'connect.NewLanguageServerServiceHandler',
               b'x-codeium-csrf-token',
               b'agy-remote-control.service',
               b'/run/user/%d/jetski_connectd.sock',
               b"BIND_HOST = '127.0.0.1'",
               b'#validateToken']:
    for off, seg in lines_of(S, marker, 1, 110):
        print(f"  @{off}: {seg.decode(errors='replace')[:190]}")
