# 09. As served: the dynamic capture (4,844-char exec prompt, 10 vs 11 tools, wire fallbacks)

**Version pin:** Factory Droid v0.245.0, 295,454,688 B, sha256 `61ad343a…fa18177cd`.
Capture: 2026-10-20. Method: `droid` ran in a sandbox HOME against a local stub; dummy
`FACTORY_API_KEY`; all endpoints pointed at `127.0.0.1`; strace-verified loopback-only,
**zero external hits**. Raw capture JSONL stays unpublished (`runs/droid/capture/`); this
finding carries the gated summary. Never contact real Factory infrastructure for this.

## WHAT WAS FOUND

- The served `droid exec` prompt assembles to **4,844 chars** and is **md5-identical across
  autonomy variants**: autonomy gates the tool-schema list, *not* the prompt text.
- Tool surface differs by provider wire format: **10 tools on the OpenAI surface, 11 on
  Anthropic** (Edit/Create split).
- Anthropic system blocks: 65 / 4,972 / 365 chars.
- Wire `fallbacks: [{claude-opus-5}]` - cross-confirms the static model registry's
  cross-vendor failover wiring (finding 05).
- OTel payload carries `user.id`, `user.email`, `organization.id` - settling the
  telemetry identity-attachment question in the affirmative.
- Session-title generator prompt captured (~3.2K); Plan/Explore spawn prompts remain static
  fragments (spawn needs a real model response).

## WHAT IT UNLOCKS

The capture is what the model actually sees at runtime, which the static corpus can't show:
autonomy changes tools, not instructions; the router's failover is real on the wire; the
OTel stream carries your identity fields with every span. The capture method (sandbox
HOME + loopback stub + strace verification) is the reusable recipe for any closed CLI.
