# 13. The 889-method RPC service map

**Trial status:** CONFIRMED. 30 services, 889 distinct methods: count recomputed directly from the per-service TSVs in `~/workspace/re-suite/findings/agy/grpc-methods-*.tsv` (sums to exactly 889; no header rows included). Supersedes the prior "341 methods" figure, which covered only the LanguageServerService and undercounted total coverage ~2.5x.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 1. WHAT WAS FOUND

**The complete RPC inventory of the binary: 889 distinct methods across 30 gRPC services**: recovered as ground truth from grpc-go codegen symbols, one `(*Unimplemented<Svc>Server).<Method>` symbol per RPC, exact names. The prior report's method census covered only the LanguageServerService (LS) and quoted 341; the full binary talks to 29 additional services. Per-service map:

| # | Service | Proto package | Methods | Direction |
|---|---|---|---|---|
| 1 | LanguageServerService | exa.language_server_pb | 350 | SERVED+CALLED |
| 2 | ApiServerService | exa.api_server_pb | 114 | CALLED |
| 3 | SeatManagementService | exa.seat_management_pb | 96 | STUBS LINKED |
| 4 | JetskiRemoteAgentProxyService | google.gca.aicode.v1main | 60 | STUBS LINKED |
| 5 | ExtensionServerService | exa.extension_server_pb | 53 | CALLED |
| 6 | PredictionService | google.cloud.aiplatform.{master,v1beta1} + google.gca.aicode.v1{main,alpha} + google.cloud.businessaicode.{v1beta,v1main} + google.internal.cloud.code.v1internal | 36 | STUBS LINKED |
| 7 | CloudCode | google.internal.cloud.code.v1internal | 23 | CALLED |
| 8 | JetskiService | google.internal.cloud.code.v1internal | 21 | CALLED |
| 9 | KnowledgeBaseService | exa.opensearch_clients_pb | 20 | STUBS LINKED |
| 10 | IndexManagementService | exa.index_pb | 19 | STUBS LINKED |
| 11 | ApiService (BOQ mesh) | devtools_jetski_boq_api_proto | 19 | CALLED |
| 12 | TaskService | google.cloud.aiplatform.v1beta1 | 14 | CALLED |
| 13 | AnalyticsService | exa.analytics_pb | 7 | STUBS LINKED |
| 14 | ManagementService | google.gca.aicode.v1main + google.cloud.businessaicode.v1beta | 7 | CALLED |
| 15 | RemotingService | exa.remoting | 7 | SERVES (connect reg) |
| 16 | ConversationService | jetski.product.v1 | 5 | SERVES (connect reg) |
| 17 | AgentService | google.cloud.aiplatform.v1beta1 | 5 | STUBS LINKED |
| 18 | IndexService | exa.index_pb | 4 | STUBS LINKED |
| 19 | CodeIndexService | exa.opensearch_clients_pb | 4 | STUBS LINKED |
| 20 | Speech | google.cloud.speech.v1p1beta1 | 3 | STUBS LINKED |
| 21 | HostBridgeService | exa.host_bridge_pb | 3 | CALLED |
| 22 | CascadePluginsService | exa.cascade_plugins_pb | 3 | STUBS LINKED |
| 23 | ContextProviderService | exa.plugin_context_pb | 3 | CALLED |
| 24 | InteractionService | genai.InteractionService | 3 | SERVES (connect reg) |
| 25 | ChatClientServerService | exa.chat_client_server_pb | 1 | STUBS LINKED |
| 26 | EvalApiServerService | exa.api_server_pb | 1 | STUBS LINKED |
| 27 | TelemetryService | google.cloud.businessaicode.v1beta | 1 | CALLED |
| 28 | DevService | exa.dev_pb | 1 | SERVES (connect reg) |
| 29 | Operations | google.longrunning | 5 | STUBS LINKED |
| 30 | S2AService | security/zatar/s2a | 1 | INFRA |
| | **TOTAL** | | **889** | |

Direction key: SERVED = `(*Server).<Method>` impls and/or `New<Svc>Handler` (connect-go registration) present; the CLI itself hosts the server. CALLED = `*<svc>Client.<Method>` impls and/or `New<Svc>Client` present: the CLI calls a remote backend. STUBS LINKED = generated `Unimplemented` symbols present, call sites not isolated this pass (the API surface exists in the binary; who calls it is unresolved). SERVES (connect reg) = connect-go handler registration present.

**The surfaces the prior pass never enumerated (+406 methods):** SeatManagementService 96 (users/teams/roles/SSO/subscription management), JetskiRemoteAgentProxyService 60 (a remote-executable mirror of the LS Cascade surface, the far side of the remote-control mesh: `StartCascade`, `SendUserCascadeMessage`, `StreamAgentStateUpdates`, terminals, triggers, plugins, permissions, Mendel flags, quota), ExtensionServerService 53 (the IDE side: `InsertCodeAtCursor`, `WriteCascadeEdit`, `ExecuteNotebook`, secret store, unified-state sync topics; the CLI *calls* the IDE), PredictionService 36 (Vertex + Gemini serving across 6 proto packages: `Predict`/`GenerateContent`/`CountTokens`/`EmbedContent`/`FetchAvailableModels`/`RetrieveUserQuota`), CloudCode 23 (`GenerateCode`, `GenerateChat`, `InternalAtomicAgenticChat`, `OnboardUser`), JetskiService 21 (`TabChat`, `CheckUrlDenylist`, `BattleModeOverrides`, `ProvisionConversationBundleDir`), KnowledgeBaseService 20 (enterprise connector ingestion: Slack/GitHub/Drive/Jira), IndexManagementService 19 (remote codebase indexing). Prior report named `jetski_service` but enumerated 0 of its 21 methods.

**Revisions to prior counts:** LS 341 -> **350** (9 clean suspects confirmed via `(*Server)` + client impls, 2 junk-glued forms cleaned (`AddEnvironmentToProject`, `UpdateAgentBrowserSubscription`) and 2 false positives KILLED: `AddEnvironmentToProjectPlugin` and `UpdateAgentBrowserSubscriptionMigration` were deconcat glue to adjacent log strings, zero impls). ApiServerService 90 -> **114** (29 missed methods found in the Unimplemented set; 5 names corrected: e.g. `GetAllowlistMigration` -> `GetAllowlist`). BOQ 18 -> **19** (`ForwardStreamProxyCommand` proven; `ProxyCommandZ`/`ListInstancesZA` are NOT RPCs: they carry a `Z<tag>` attribute byte in the custom descriptor table, semantics UNRESOLVED). Dated note: the rigor lane independently counts LS at 348 (method-vs-symbol counting delta); the Unimplemented-symbol count of 350 is the method inventory.

**Hard limits, stated plainly:** **no self-describing subcommand exists**: unlike codex's `generate-json-schema`, `agy --help` and all 12 subcommand helps were enumerated read-only and no RPC-introspection verb exists. Per-method JSON schemas remain unrecoverable: proto descriptors are stripped, so method NAMES are fully recoverable but field shapes are not (only `XxxRequest`/`XxxResponse` type names, via the BOQ custom descriptor table and Go generic instantiations elsewhere). One single-occurrence anomaly (`/exa.seat_management_pb.SeatManagementService/GetRoles` @92144512, no Unimplemented symbol, likely stale/renamed vs `GetRolesForUser`) was NOT counted. `AgentService` (aiplatform v1beta1, 5 stubs) is adjudicated as vendored client stubs, not a product surface.

---

## 2. HOW IT WAS FOUND

Source priority, in order (lane DEPTH-GRPC): (1) `(*Unimplemented<Svc>Server).<Method>` symbols from grpc-go codegen; exactly one per RPC, EXACT names; (2) `(*<Svc>HandlerHook)._<Svc>_<Method>_Handler` symbols (grpc-go ServiceDesc); (3) `(*Server).<Method>` / `*<svc>Client.<Method>` impl sets for direction; (4) Connect procedure-table runs (`/<pkg>.<Svc>/<Method>` back-to-back). Deconcat maximal-identifier runs were treated SUSPECT until confirmed by 1–3: this killed the 2 prior false positives.

Exact commands (all read-only, 2026-10-19, against sha256-verified binary):
- `sha256sum /home/hatch/.local/bin/agy` -> `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`
- `strings -a -t d /home/hatch/.local/bin/agy > agy.strings.txt` (66MB, 1,924,440 lines; first column = rodata file byte offset, cited as `@N`)
- Method extraction: python regex `([a-zA-Z0-9_./-]+?)\.\(\*Unimplemented([A-Za-z0-9_]+?)Server\)\.([A-Za-z0-9_]+?)(?:-fm|\.func1)?(?:\s|$)` over the strings file, first-occurrence offsets, dedup by method; per-service TSVs at `~/workspace/re-suite/findings/agy/grpc-methods-*.tsv`
- Hook cross-check: `\(\*LanguageServerServiceHandlerHook\)\._LanguageServerService_([A-Za-z0-9_]*)_Handler`
- Direction: pclntab scans for `New<Svc>Client`, `New<Svc>Handler`, `(*<recv>Client).<Method>`, `(*Server).<Method>` (164,366-function table, independent re-parse)
- BOQ descriptor table: `awk '$1>=95224045 && $1<=95229200' agy.strings.txt`; per-method Request/Response type names, `/$rpc/` paths, `/v1internal:` REST transcoding paths (e.g. `/v1internal:proxyCommand/{target_instance_uuid}/{rpc_path=**}` @95226264), streaming kinds from Go generics (`grpc.BidiStreamingServer[...ConnectInstanceRequest,...]`)
- No-self-describing-subcommand check: `for sub in agent agents changelog help install mcp mic-serve models plugin plugins remote-control update; do agy $sub --help; done` (read-only)
- Prior baseline read first: `~/workspace/rea-agy/deep-dive/pocs/a1_inventory.txt` (extended, not duplicated)

---

## 3. WHAT IT UNLOCKS

The CLI isn't one agent program with a backend: it's a full protocol nervous system with 889 named endpoints. Previous coverage mapped only the agent-brain surface (the language server); the map now shows the CLI also ships user/team/seat management, enterprise SSO, a remote-control mirror that lets a server drive your agent sessions from the other side, a code-assist backend, Vertex agent-engine tasks, enterprise knowledge connectors that ingest Slack/GitHub/Drive/Jira, speech-to-text, and a mesh control plane with REST-transcoded RPC paths. Anyone reverse-engineering the wire protocol now starts from a complete endpoint census instead of guessing: names, which side serves, and which direction traffic flows are all pinned. The hard limit is honest too: you can name every endpoint, but the request shapes are stripped from the binary, so a full third-party reimplementation of the client still needs the live server's descriptor traffic.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Wire-protocol census:** `~/workspace/re-suite/findings/agy/grpc-methods-*.tsv` (30 machine-readable tables: method, first rodata offset). The LS table is the local localhost:5387 surface (recipe in repo doc 01); ApiServerService/CloudCode/JetskiService are the remote backend contract.
- **Remote-control far side:** `JetskiRemoteAgentProxyService` (60 methods, `google.gca.aicode.v1main`) is the server-side mirror of the agent surface: start any remote-agent research there; the BOQ `ApiService` (19, `devtools_jetski_boq_api_proto`) is the transport mesh under it, with `/v1internal:` REST transcoding paths recoverable from rodata 95224045–95229200.
- **IDE-side contract:** `ExtensionServerService` (53) lists every call the CLI can make into the Antigravity IDE extension (`WriteCascadeEdit`, `ExecuteNotebook`, `StoreSecretValue`, `SubscribeToUnifiedStateSyncTopic`/`PushUnifiedStateSyncUpdate`): the spec for a compatible third-party IDE integration.
- **Field-shape recovery:** BOQ is the only service with a hand-rolled descriptor table (per-method Request/Response type names + transcoding paths); everywhere else, generic instantiations (`grpc.BidiStreamingServer[...Request,...Response]`) and the stripped proto descriptors are the only shape evidence. Do not quote field shapes you cannot verify: names are the ground truth.
- **Do not cite as methods:** `ProxyCommandZ`, `ListInstancesZA` (Z-tagged descriptor entries, not RPCs); `GetRoles` on SeatManagementService (single-occurrence anomaly, no symbol, uncounted).
