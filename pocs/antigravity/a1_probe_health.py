#!/usr/bin/env python3
"""A1 lane bonus PoC: read-only handshake probe for the agy LanguageServer.
Single GET /healthz to the LS address (ANTIGRAVITY_LS_ADDRESS, default
localhost:5387), 2s timeout, no auth, no writes, no retries. Reports presence
and banner only. Exits 0 even when the LS is not running (that is a result).
"""
import os, socket, sys, urllib.request

addr = os.environ.get("ANTIGRAVITY_LS_ADDRESS", "localhost:5387")
url = f"http://{addr}/healthz"
print(f"probe: GET {url} (timeout 2s, single attempt)")
try:
    with urllib.request.urlopen(url, timeout=2) as r:
        body = r.read(400).decode(errors="replace")
        print(f"ALIVE: status={r.status} body={body!r}")
        print("server speaks HTTP on the LS port; try POST "
              f"http://{addr}/exa.language_server_pb.LanguageServerService/<Method> "
              "with Content-Type: application/json and x-codeium-csrf-token header "
              "(Connect unary protocol) for method-level probing.")
except Exception as e:
    print(f"NOT RUNNING: {type(e).__name__}: {e}")
