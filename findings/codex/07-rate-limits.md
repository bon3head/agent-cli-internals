# 07. Rate limits are readable AND redeemable

**Version pin:** all method shapes from the **0.149.0** schema set
(`~/workspace/rea-codex/app-server-schema/v2/`). Strings context (plan-type enums,
token-budget triggers) from the **0.155.1** binary. Live quota behavior is UNVERIFIED:
no `account/rateLimits/read` call was made and no network traffic was observed.

## 1. WHAT WAS FOUND

Quota management is a first-class protocol surface, not just error codes:

**Read the snapshot**: `account/rateLimits/read` → `GetAccountRateLimitsResponse`:
`RateLimitSnapshot{ limitId, limitName, planType, primary: RateLimitWindow, secondary:
RateLimitWindow, credits: CreditsSnapshot, individualLimit: SpendControlLimitSnapshot,
rateLimitReachedType, spendControlReached }` plus top-level `additional_rate_limits`,
`rate_limit_reset_credits`, `rate_limit_upsell`, `account_id`, `user_id`, `plan_type`.
- `RateLimitWindow{ usedPercent (int, required), resetsAt (unix sec, nullable), windowDurationMins (nullable) }`
- `CreditsSnapshot{ hasCredits, unlimited, balance (string, nullable) }`
- `SpendControlLimitSnapshot{ limit, used (strings), remainingPercent, resetsAt }`
- `PlanType` enum: `free go plus pro prolite team self_serve_business_prolite
  self_serve_business_usage_based business ent26 enterprise_cbp_automation
  enterprise_cbp_usage_based enterprise edu edu_plus edu_pro unknown` (CONFIRMED, 0.149.0 schema)
- `RateLimitReachedType`: `rate_limit_reached`, `workspace_owner_credits_depleted`,
  `workspace_member_credits_depleted`, `workspace_owner_usage_limit_reached`,
  `workspace_member_usage_limit_reached`

**Push updates are sparse merges**: `account/rateLimits/updated{rateLimits}` is a sparse
rolling update. The schema contract says: "Clients should merge available values into the
most recent `account/rateLimits/read` response or refetch that snapshot." Refetching on
every update is wasteful *by schema contract*.

**Redeem reset credits**: `account/rateLimitResetCredit/consume`:
- Params: `{creditId? (opaque, optional; backend selects when omitted), idempotencyKey (required, UUID recommended)}`
- Response: `outcome ∈ {reset | nothingToReset | noCredit | alreadyRedeemed}`
- Credit object: `{id, resetType ∈ {codexRateLimits, unknown}, status ∈ {available, redeeming, redeemed, unknown}, grantedAt, expiresAt?, title?, description?}`; summary `{availableCount, credits?}` (backend may cap list length)

**Usage**: `account/usage/read{threadId?}` (thread-scoped estimate when present, else
account-wide) → `AccountTokenUsageSummary{ lifetimeTokens, currentStreakDays,
longestStreakDays, peakDailyTokens, longestRunningTurnSec }` +
`AccountTokenUsageDailyBucket[]{ startDate, tokens }` + `ThreadUsage{ threadId,
estimatedUsageCreditsMicros, estimatedUsageUsdMicros, groups[] }`.

**Enforcement is real, not advisory (0.155.1 strings, CONFIRMED):** a SQLite trigger
fires auto-compaction: `WHEN ? = 'active' AND token_budget IS NOT NULL AND tokens_used >=
token_budget THEN ?`. Separate `rollout_budget` metering exists in "rollout budget units"
with reminder thresholds. Turn failure taxonomy (schema enum): `ContextWindowExceeded |
SessionBudgetExceeded | UsageLimitExceeded | RateLimitExceeded | CyberPolicyMisalignment |
PolicyViolation | Http`. The TUI status bar caches rate-limit state (`status history
rate-limit state poisoned` error-cache marker); display keys primary/secondary windows
per model slug, and memories startup is gated on quota (`skipping memories startup
because Codex rate limits are below the configured threshold`).

**CONFIRMED vs INFERENCE:** all shapes above are CONFIRMED from the 0.149.0 schema; the
SQLite token-budget trigger and plan-type values are CONFIRMED from 0.155.1 strings. Live
behavior (whether reads are persisted to disk (no obvious cache file found; state likely
lives in the daemon/TUI process), how credits are granted, and whether the consume call
works headless) is UNVERIFIED.

## 2. HOW IT WAS FOUND

Lane C (auth-sessions), 0.155.1 binary strings + the 0.149.0 schema files
(`ConsumeAccountRateLimitResetCreditParams/Response.json`,
`AccountRateLimitsUpdatedNotification.json`, `ErrorNotification.json` for the failure
taxonomy). Plan-type enum cross-checked against the `KnownPlan` strings (`gopro`,
`prolite`, `self_serve_business_prolite`, `cbp_automation`, ...). No live
`account/rateLimits/read` was invoked; no network calls made.

## 3. WHAT IT UNLOCKS

A driver can watch its own quota instead of blindly hitting walls: read the snapshot once,
merge sparse push updates, route heavy work to quiet windows (`resetsAt`), and even
*redeem reset credits* programmatically: quota recovery becomes an API call with an
idempotency key, not a support ticket. Usage reads give per-thread cost estimates
(`estimatedUsageUsdMicros`) for billing dashboards.

## 4. HOW A DEVELOPER BUILDS ON IT

1. On session start: `account/rateLimits/read` → store the snapshot; subscribe to
   `account/rateLimits/updated` and merge (do not refetch every update: the schema says so).
2. Gate dispatch: check `primary.usedPercent` / `secondary.usedPercent` per model slug and
   `resetsAt` before launching expensive turns; set per-thread goals with
   `thread/goal/set{tokenBudget}` (Finding 01) and let the server auto-compact when the
   SQLite trigger fires.
3. Credit redemption (safe to retry): `account/rateLimitResetCredit/consume{idempotencyKey:
   <fresh UUID>}`; interpret `reset` (success), `nothingToReset`, `noCredit`,
   `alreadyRedeemed` (duplicate of a previous redemption).
4. Cost tracking: `account/usage/read{threadId}` per turn for `estimatedUsageUsdMicros` /
   `estimatedUsageCreditsMicros`; account-wide for daily buckets.
5. Handle `error{error: TurnError, willRetry}` with the failure taxonomy: `RateLimitExceeded`
   vs `SessionBudgetExceeded` vs `UsageLimitExceeded` demand different backoff/credit logic.
