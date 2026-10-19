# 03 — Model catalog: server-driven, 4-tier waterfall, 39-entry alias map

**Trial status:** CONFIRMED at suite level (17/17 on the same binary). Not separately re-trialed; stands on lane A5 evidence below.

---

## 1. WHAT WAS FOUND

The CLI's model list is not hardcoded — it is pushed by the server via `FetchAvailableModels` on `google.internal.cloud.code.v1internal`. Byte evidence:

- Service: `google.internal.cloud.code.v1internal` prediction service (`FetchAvailableModelsRequest/Response` at strings :55862-55871).
- Request fields: `GetEntitlement, GetLocation, GetProject, GetRequestId` — catalog is per-user rollout capable.
- Response fields: `GetModels, GetDefaultAgentModelId, GetAgentModelSorts, GetCommandModelIds, GetTabModelIds, GetBattleModeModelSorts, GetCommitMessageModelIds, GetDeprecatedModelIds, GetExperimentIds, GetImageGenerationModelIds, GetMqueryModelIds, GetTieredModelIds, GetWebSearchModelIds, GetAudioTranscriptionModelIds`.
- `ModelDetails` has ~50 server-tunable fields (`GetDisplayName, GetMaxTokens, GetThinkingBudget, GetSupportsThinking, GetBeta, GetIsInternal, GetQuotaInfo, GetModelExperiments…`), plus retirement machinery: `DeprecatedModelReroutingInfo{GetOldModelEnum, GetNewModelEnum, GetNewModelId}` — server-side model deprecation with automatic rerouting.

Client resolution is a **4-tier waterfall** (log strings, byte-exact):

```
[ModelConfig] Resolving models from Tier 1 (Inline admin_settings models.list)
→ Tier 2 (Remote catalog listSource: %s)
→ Tier 3 (Gateway discovery at %s, wireProtocol: %s)
→ Tier 4 built-in default
```

(Tier 3 is the AGY_LLM_GATEWAY_* custom-model path — see finding 12.)

**Alias map (CONFIRMED):** `MODEL_PLACEHOLDER_M*` enum is M0..M1650 contiguous (1651 slots, zero gaps). The binary does NOT hold a full mapping (canonicals resolve server-side); it does hold a 53-entry alias table (strings :1611072-1611100, decoded to `deep-dive/model-alias-map.json`, 39 non-identity entries). Byte-exact samples:

- `MODEL_PLACEHOLDER_M18` → `MODEL_GOOGLE_GEMINI_2_5_PRO`, `M148` → PRO
- `MODEL_PLACEHOLDER_M50` → `MODEL_GOOGLE_GEMINI_2_5_FLASH`, `M198` → FLASH
- `MODEL_PLACEHOLDER_M15/M20/M84/M133/M186/M187/M262/M270` → `M132`
- `MODEL_PLACEHOLDER_M317/M318/M319/M320/M322/M78` → `M124`
- `MODEL_PLACEHOLDER_M401..M405` → `M400`; `M409..M413/M417..M421` → `M408`
- `MODEL_PLACEHOLDER_M47/M271` → `M269`; `M35` → `M26`; `M292` → `M291`
- `MODEL_GOOGLE_GEMINI_2_5_FLASH_LITE` → `MODEL_GOOGLE_GEMINI_2_5_FLASH`
- `MODEL_GOOGLE_GEMINI_2_5_FLASH_THINKING` → `MODEL_GOOGLE_GEMINI_2_5_FLASH`

INFERENCE: M132/M124 are high-fan-in canonical serving buckets (many aliases collapse into them), likely the current pro/flash serving aliases. Full M0..M1650→model mapping from the binary is impossible — KILLED, server-side only.

Target pinned: `agy` v1.3.1, sha256 `085f43e0d0628a8a8dabe1e547067818fa2c0adc86cfac98a3c4492918f455ef`.

---

## 2. HOW IT WAS FOUND

Lane A5 (internal intel), strings tier. The `FetchAvailableModels` service and its ~50-field `ModelDetails` were extracted from proto descriptor remnants and `Get*` getter symbols; the 4-tier waterfall decoded from `[ModelConfig]` log strings at :347310/:347249. The alias map was carved from strings :1611072-1611100 into `deep-dive/model-alias-map.json`. The M0..M1650 contiguity claim came from a regex count over `agy.strings` (1651 slots, zero gaps). The "no full mapping" kill was verified by exhaustive search: only the 53-entry table exists statically.

---

## 3. WHAT IT UNLOCKS

The model picker in the CLI is a control panel with four layers: your own admin settings win first, then Google's server-pushed catalog, then a custom model gateway, then a built-in fallback. That means Google can add, rename, deprecate, or reroute models on your machine without you updating anything — and the alias table explains why a model ID like "M18" silently resolves to Gemini 2.5 Pro. It also means you can insert your own layer: point Tier 3 at your own model endpoint.

---

## 4. HOW A DEVELOPER BUILDS ON IT

- **Force a model resolution tier:** set `models.list` inline in `admin_settings` to bypass the server catalog (Tier 1 wins); or see finding 12 for the Tier 3 gateway path.
- **Read deprecations:** watch `GetDeprecatedModelIds` and `DeprecatedModelReroutingInfo{old_model_enum, new_model_enum, new_model_id}` in the catalog response — rerouting is automatic and server-driven.
- **Per-surface sorts:** the catalog pushes `agent/command/tab/battle-mode/commit-message/image-gen/mquery/websearch` model sort lists — pin different models per surface via these fields.
- **Alias debugging:** when the CLI logs a `MODEL_PLACEHOLDER_M*` enum, resolve it through `deep-dive/model-alias-map.json` (39 non-identity entries decoded from the binary).
- **Tier slots:** custom gateway models consume placeholder slots — `[ModelConfig] %d custom gateway model(s) exceeded the maximum placeholder limit` is the overflow signal.
