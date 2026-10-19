#!/usr/bin/env python3
"""A3 PoC: antigravity oauth-token inspector (REA lane A3, auth & identity).

Reads the user's OWN ~/.gemini/antigravity-cli/antigravity-oauth-token and
prints ONLY non-secret metadata. Secret values (access_token, refresh_token,
id_token payload) are NEVER printed, logged, or hashed.

Evidence tier: read-only behavioral inspection of the credential store.
"""
import json, os, sys, stat
from datetime import datetime, timezone

TOKEN_PATH = os.path.expanduser(
    "~/.gemini/antigravity-cli/antigravity-oauth-token")


def mask(v: str) -> str:
    """Describe a secret string's shape without revealing any content."""
    if not isinstance(v, str):
        return f"<{type(v).__name__}>"
    classes = []
    if v.isascii():
        classes.append("ascii")
    return "value[str len=%d]" % len(v)


def main() -> int:
    st = os.stat(TOKEN_PATH)
    print("path:", TOKEN_PATH)
    print("mode:", oct(stat.S_IMODE(st.st_mode)), "(owner-only)" if stat.S_IMODE(st.st_mode) == 0o600 else "")
    print("size_bytes:", st.st_size)

    with open(TOKEN_PATH) as f:
        data = json.load(f)

    print("\ntop-level fields:", sorted(data.keys()))
    tok = data.get("token", {})
    print("token fields:", sorted(tok.keys()))
    print("token_type:", tok.get("token_type"))           # 'Bearer' - non-secret
    print("access_token_shape:", mask(tok.get("access_token", "")))
    print("refresh_token_shape:", mask(tok.get("refresh_token", "")))
    print("expiry:", tok.get("expiry"))                   # timestamp - explicitly non-secret
    try:
        exp = datetime.fromisoformat(str(tok["expiry"]).replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = (exp - now).total_seconds()
        print("expiry_status:", "EXPIRED" if delta < 0 else "VALID",
              f"(delta_hours={delta / 3600:.1f})")
    except Exception as e:
        print("expiry_status: UNPARSEABLE (%s)" % e)

    print("auth_method:", data.get("auth_method"))         # e.g. 'oauth2' - non-secret

    # id_token is a JWT: decode the HEADER only (alg/typ/kid are non-secret).
    # The payload (email, sub) is never touched.
    idt = data.get("id_token", "")
    print("id_token_shape:", mask(idt))
    parts = idt.split(".")
    print("id_token_segments:", len(parts))
    if len(parts) == 3:
        import base64
        pad = "=" * (-len(parts[0]) % 4)
        hdr = json.loads(base64.urlsafe_b64decode(parts[0] + pad))
        print("id_token_header:", {k: hdr[k] for k in ("alg", "typ", "kid") if k in hdr})

    print("\nconclusion: standard golang.org/x/oauth2 token JSON "
          "(access_token/refresh_token/expiry/token_type) + auth_method + id_token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
