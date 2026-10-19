# Claude Code CLI cloud+gateway reference (static extraction)

Source: `/home/hatch/.local/bin/claude` — printable-run scan, no execution, no network.

## Cloud session / runner / bridge endpoints (19)

| value | hits |
|---|---|
| `/v1/code/memory/` | 2 |
| `/v1/code/triggers` | 2 |
| `/v1/code/triggers/${l}` | 2 |
| `/v1/code/` | 1 |
| `/v1/code/agent-proxy` | 1 |
| `/v1/code/github/import-token` | 1 |
| `/v1/code/github/post-review-comment` | 1 |
| `/v1/code/local/memory/credential` | 1 |
| `/v1/code/local/memory/mounts` | 1 |
| `/v1/code/mcp/hearthbot` | 1 |
| `/v1/code/scm-connectors/{provider}/{id}/tunnel` | 1 |
| `/v1/code/sessions/` | 1 |
| `/v1/code/sessions/${e.sessionId}/device` | 1 |
| `/v1/code/sessions/${e}` | 1 |
| `/v1/code/sessions/${e}/device` | 1 |
| `/v1/code/sessions/${n}/agent-proxy` | 1 |
| `/v1/code/sessions/${o}/worker/otlp/${e}` | 1 |
| `/v1/code/triggers/${l}/run` | 1 |
| `/v1/code/webhook-triggers` | 1 |

## OAuth / settings / misc API paths (78)

| value | hits |
|---|---|
| `/api/hello` | 7 |
| `/api/desktop/` | 3 |
| `/api/model_selector/${o}` | 3 |
| `/api/oauth/account/settings` | 3 |
| `/api/` | 2 |
| `/api/event_logging/` | 2 |
| `/api/frame/contract/latest` | 2 |
| `/api/frame/deploy/direct` | 2 |
| `/api/frame/deploy/prepare` | 2 |
| `/api/oauth/organizations/:orgUUID/overage_spend_limit` | 2 |
| `/api/oauth/usage` | 2 |
| `/api/organizations/:orgUUID/claude_code/onboarding` | 2 |
| `/oauth/device_authorization` | 2 |
| `/oauth/token` | 2 |
| `/api/claude_cli_feedback` | 1 |
| `/api/claude_code/notification/preferences` | 1 |
| `/api/claude_code/organizations/metrics_enabled` | 1 |
| `/api/claude_code/policy_limits` | 1 |
| `/api/claude_code/skills` | 1 |
| `/api/claude_code_grove` | 1 |
| `/api/claude_code_shared_session_transcripts` | 1 |
| `/api/directory/plugins` | 1 |
| `/api/event_logging/v2/batch` | 1 |
| `/api/frame/` | 1 |
| `/api/frame/blob/${e}/${r}/agent-delete` | 1 |
| `/api/frame/blob/${e}/agent-copy` | 1 |
| `/api/frame/blob/${e}/agent-list` | 1 |
| `/api/frame/blob/${e}/agent-upload` | 1 |
| `/api/frame/contract/${e.version}` | 1 |
| `/api/frame/contract/${e}/${n}.d.ts` | 1 |
| `/api/frame/contract/${e}/prompt` | 1 |
| `/api/frame/db/agent` | 1 |
| `/api/frame/diag/${e.slug}/${n.ver}` | 1 |
| `/api/frame/frames/external` | 1 |
| `/api/frame/subscribe/${e}` | 1 |
| `/api/frame/sync` | 1 |
| `/api/frame/track` | 1 |
| `/api/frame/types` | 1 |
| `/api/frame/unsubscribe/${e}` | 1 |
| `/api/frame/upload` | 1 |
| `/api/hello/:name` | 1 |
| `/api/oauth/account/grove_notice_viewed` | 1 |
| `/api/oauth/organizations/:orgUUID/admin_requests` | 1 |
| `/api/oauth/organizations/:orgUUID/billing/tax_rate` | 1 |
| `/api/oauth/organizations/:orgUUID/claude_code/pro_trial` | 1 |
| `/api/oauth/organizations/:orgUUID/contracts/auto_reload_settings` | 1 |
| `/api/oauth/organizations/:orgUUID/contracts/prepaid/credits` | 1 |
| `/api/oauth/organizations/:orgUUID/marketplaces` | 1 |
| `/api/oauth/organizations/:orgUUID/mcp/connectors/list` | 1 |
| `/api/oauth/organizations/:orgUUID/mcp/connectors/search` | 1 |
| `/api/oauth/organizations/:orgUUID/mcp/connectors/suggest` | 1 |
| `/api/oauth/organizations/:orgUUID/overage_credit_grant` | 1 |
| `/api/oauth/organizations/:orgUUID/payment_method` | 1 |
| `/api/oauth/organizations/:orgUUID/plugin_ratings` | 1 |
| `/api/oauth/organizations/:orgUUID/plugin_ratings/appearances` | 1 |
| `/api/oauth/organizations/:orgUUID/plugin_ratings/appearances/outcome` | 1 |
| `/api/oauth/organizations/:orgUUID/plugins/` | 1 |
| `/api/oauth/organizations/:orgUUID/plugins/search` | 1 |
| `/api/oauth/organizations/:orgUUID/prepaid/bundles` | 1 |
| `/api/oauth/organizations/:orgUUID/prepaid/commits/${e}` | 1 |
| `/api/oauth/organizations/:orgUUID/prepaid/credits` | 1 |
| `/api/oauth/organizations/:orgUUID/setup_overage_billing` | 1 |
| `/api/oauth/organizations/:orgUUID/skills/search` | 1 |
| `/api/oauth/organizations/:orgUUID/sync/github/auth` | 1 |
| `/api/organization/claude_code_first_token_date` | 1 |
| `/api/organizations/${m}/reset_rate_limits` | 1 |
| `/api/organizations/${s}/reset_rate_limits` | 1 |
| `/api/organizations/:orgUUID/cowork/remote_devices` | 1 |
| `/api/organizations/:orgUUID/marketplace/plugin-assets/${e}` | 1 |
| `/api/organizations/:orgUUID/model_selector/${o}` | 1 |
| `/api/organizations/:orgUUID/model_selector_state/${o}` | 1 |
| `/api/users/:id` | 1 |
| `/api/v4/` | 1 |
| `/api/ws/speech_to_text/voice_stream` | 1 |
| `/managed/settings` | 1 |
| `/oauth/callback` | 1 |
| `/user` | 1 |
| `/user/bootstrap` | 1 |

## Cloud-related CLI flags (18)

| value | hits |
|---|---|
| `--cloud` | 129 |
| `--file` | 59 |
| `--sdk-url` | 46 |
| `--environment` | 44 |
| `--session-id` | 42 |
| `--watch-artifact` | 34 |
| `--teleport` | 29 |
| `--remote` | 26 |
| `--await-claim` | 21 |
| `--project` | 21 |
| `--ref` | 18 |
| `--attach-serve` | 16 |
| `--on-branch` | 15 |
| `--watch-artifact-no-autoreact` | 13 |
| `--init-only` | 11 |
| `--pool` | 11 |
| `--client-data-url` | 9 |
| `--correlation-id` | 8 |

## Cloud/gateway env vars (18)

| value | hits |
|---|---|
| `ANTHROPIC_API_KEY` | 144 |
| `ANTHROPIC_BASE_URL` | 116 |
| `ANTHROPIC_AUTH_TOKEN` | 70 |
| `CLAUDE_CODE_SESSION_ACCESS_TOKEN` | 55 |
| `CLAUDE_CODE_SESSION_KIND` | 52 |
| `CLAUDE_CODE_USE_GATEWAY` | 25 |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | 20 |
| `SELF_HOSTED_RUNNER_ENVIRONMENT_SECRET` | 20 |
| `SELF_HOSTED_RUNNER_POOL_SECRET` | 16 |
| `CLAUDE_CODE_SESSION_ID` | 14 |
| `CLAUDE_CODE_CLIENT_DATA_URL` | 11 |
| `CLAUDE_CODE_SESSION_ATTENDED` | 8 |
| `CLAUDE_CODE_SESSION_NAME` | 7 |
| `CLAUDE_CODE_SESSION_ORIGIN` | 7 |
| `CLAUDE_CODE_SESSION_LOG` | 3 |
| `CLAUDE_CODE_SESSION_START_ANNOUNCEMENTS_BEFORE_PROMPT` | 3 |
| `CLAUDE_CODE_ULTRAREVIEW_PREFLIGHT_FIXTURE` | 3 |
| `CLAUDE_CODE_ULTRAREVIEW_QUOTA_FIXTURE` | 3 |

## Session / environment id prefixes (3)

| value | hits |
|---|---|
| `session_` | 1222 |
| `cse_` | 39 |
| `ccpool_` | 13 |

## Gateway config / policy keys (6)

| value | hits |
|---|---|
| `allowedProviders` | 94 |
| `forceLoginMethod` | 42 |
| `forceLoginOrgUUID` | 40 |
| `forceLoginGatewayUrl` | 28 |
| `gatewayInternalNetworks` | 21 |
| `serve_to_desktop` | 16 |

## First-party hosts (145)

| value | hits |
|---|---|
| `https://code.claude.com/docs/en/legal-and-compliance.` | 2158 |
| `https://code.claude.com/docs/en/overview` | 289 |
| `https://claude.ai/code` | 18 |
| `https://api.anthropic.com` | 15 |
| `https://code.claude.com/docs/en/hooks` | 12 |
| `https://code.claude.com/docs/en/sandboxing` | 10 |
| `https://www.anthropic.com/legal/aup` | 10 |
| `https://code.claude.com/docs/en/ultrareview.` | 9 |
| `https://code.claude.com/docs/en/security` | 8 |
| `https://code.claude.com/docs/en/mcp` | 7 |
| `https://claude.ai/settings/data-privacy-controls` | 6 |
| `https://code.claude.com/docs/en/microsoft-foundry` | 6 |
| `https://code.claude.com/docs/en/sandboxing.` | 6 |
| `https://claude.ai` | 5 |
| `https://claude.ai/customize/connectors` | 5 |
| `https://claude.ai/customize/connectors.` | 5 |
| `https://code.claude.com/docs/en/network-config` | 5 |
| `https://api-staging.anthropic.com` | 4 |
| `https://code.claude.com/docs/en/cli-reference` | 4 |
| `https://code.claude.com/docs/en/model-config` | 4 |
| `https://code.claude.com/docs/en/monitoring-usage` | 4 |
| `https://anthropic.com/legal/privacy` | 3 |
| `https://anthropic.com/legal/terms` | 3 |
| `https://api.anthropic.com/` | 3 |
| `https://api.anthropic.com/api/oauth/cri` | 3 |
| `https://claude.ai/code/artifact/` | 3 |
| `https://code.claude.com/docs/en/chrome` | 3 |
| `https://code.claude.com/docs/en/claude-code-on-the-web` | 3 |
| `https://code.claude.com/docs/en/claude_code_docs_map.md` | 3 |
| `https://code.claude.com/docs/en/keybindings` | 3 |
| `https://docs.anthropic.com/en/docs/resources/model-deprecations` | 3 |
| `https://downloads.claude.ai/claude-code-releases` | 3 |
| `https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking` | 3 |
| `https://platform.claude.com/llms.txt` | 3 |
| `https://www.anthropic.com/news/updates-to-our-consumer-terms` | 3 |
| `https://anthropic.com/claude-code/plugin.schema.json` | 2 |
| `https://anthropic.com/supported-countries` | 2 |
| `https://api.anthropic.com/api/event_logging/v2/batch` | 2 |
| `https://api.anthropic.com/api/oauth/claude_cli/create_api_key` | 2 |
| `https://claude.ai/admin-settings/claude-tag` | 2 |
| `https://claude.ai/admin-settings/usage` | 2 |
| `https://claude.ai/api/desktop/darwin/universal/dmg/latest/redirect` | 2 |
| `https://claude.ai/api/desktop/win32/x64/exe/latest/redirect` | 2 |
| `https://claude.ai/chrome` | 2 |
| `https://claude.ai/code/onboarding?magic=env-setup` | 2 |
| `https://claude.ai/code/onboarding?magic=github-app-setup.` | 2 |
| `https://claude.ai/code/routines` | 2 |
| `https://claude.ai/code/routines.` | 2 |
| `https://claude.ai/design?utm_source=claude_code&utm_medium=tip&utm_campaign=tengu_cedar_plume` | 2 |
| `https://claude.ai/download` | 2 |
| `https://claude.ai/install.sh` | 2 |
| `https://claude.ai/mobile?entrypoint=claude_code_cli` | 2 |
| `https://claude.ai/oauth/claude-code-client-metadata` | 2 |
| `https://claude.ai/settings/usage` | 2 |
| `https://claude.ai/settings/usage?from=cc_cli_limit_message` | 2 |
| `https://code.claude.com/docs/en` | 2 |
| `https://code.claude.com/docs/en/amazon-bedrock` | 2 |
| `https://code.claude.com/docs/en/auto-mode-classifier-billing` | 2 |
| `https://code.claude.com/docs/en/changelog` | 2 |
| `https://code.claude.com/docs/en/claude-platform-on-aws` | 2 |
| `https://code.claude.com/docs/en/costs` | 2 |
| `https://code.claude.com/docs/en/data-usage` | 2 |
| `https://code.claude.com/docs/en/fast-mode` | 2 |
| `https://code.claude.com/docs/en/google-vertex-ai` | 2 |
| `https://code.claude.com/docs/en/jetbrains` | 2 |
| `https://code.claude.com/docs/en/memory` | 2 |
| `https://code.claude.com/docs/en/permission-modes` | 2 |
| `https://code.claude.com/docs/en/remote-control` | 2 |
| `https://code.claude.com/docs/en/settings` | 2 |
| `https://code.claude.com/docs/en/sub-agents` | 2 |
| `https://code.claude.com/docs/s/claude-code-auto-mode` | 2 |
| `https://downloads.claude.ai` | 2 |
| `https://downloads.claude.ai/` | 2 |
| `https://downloads.claude.ai/model-catalog/v1/catalog.json` | 2 |
| `https://downloads.claude.ai/model-catalog/v1/schema.json` | 2 |
| `https://mcp-proxy.anthropic.com` | 2 |
| `https://platform.claude.com/buy_credits?returnUrl=/oauth/code/success%3Fapp%3Dclaude-code` | 2 |
| `https://platform.claude.com/docs/en/api/messages` | 2 |
| `https://platform.claude.com/docs/en/build-with-claude/compaction` | 2 |
| `https://platform.claude.com/docs/en/build-with-claude/preserved-thinking` | 2 |
| `https://platform.claude.com/oauth/authorize` | 2 |
| `https://platform.claude.com/oauth/code/callback` | 2 |
| `https://platform.claude.com/oauth/code/success?app=claude-code` | 2 |
| `https://platform.claude.com/settings/billing` | 2 |
| `https://platform.claude.com/v1/oauth/token` | 2 |
| `https://support.anthropic.com/` | 2 |
| `https://www.anthropic.com/claude/fable` | 2 |
| `https://www.anthropic.com/legal/consumer-terms` | 2 |
| `https://www.anthropic.com/legal/promotion-terms` | 2 |
| `https://www.anthropic.com/news/` | 2 |
| `https://www.anthropic.com/news/claude-fable-5-mythos-5` | 2 |
| `https://api.anthropic.com/api/oauth/claude_cli/roles` | 1 |
| `https://api.anthropic.com/api/oauth/claude_cli/rolesY` | 1 |
| `https://api.anthropic.com/api/web/domain_info?domain=` | 1 |
| `https://api.anthropic.com/api/web/domain_info?domain=${encodeURIComponent` | 1 |
| `https://claude.ai/code.` | 1 |
| `https://claude.ai/code.p` | 1 |
| `https://claude.ai/code/artifact/${S.slug}` | 1 |
| `https://claude.ai/code/artifact/${g.slug}` | 1 |
| `https://claude.ai/code/artifact/${g}` | 1 |
| `https://claude.ai/code/artifact/${r.slug}` | 1 |
| `https://claude.ai/code/onboarding?magic=github-app-setup` | 1 |
| `https://claude.ai/code/routines/{ROUTINE_ID}` | 1 |
| `https://claude.ai/customize/connectors.r` | 1 |
| `https://claude.ai/restricted` | 1 |
| `https://claude.ai/restrictedK` | 1 |
| `https://claude.ai/upgrade/max?utm_source=claude_code&utm_medium=cli&utm_campaign=` | 1 |
| `https://claude.ai/upgrade/max?utm_source=claude_code&utm_medium=cli&utm_campaign=${a}` | 1 |
| `https://code.claude.com/docs.` | 1 |
| `https://code.claude.com/docs/en/amazon-bedrock.md` | 1 |
| `https://code.claude.com/docs/en/changelog.md` | 1 |
| `https://code.claude.com/docs/en/channels-reference.` | 1 |
| `https://code.claude.com/docs/en/claude-code-on-the-web.md` | 1 |
| `https://code.claude.com/docs/en/claude-directory.md` | 1 |
| `https://code.claude.com/docs/en/cli-reference.md` | 1 |
| `https://code.claude.com/docs/en/commands.md` | 1 |
| `https://code.claude.com/docs/en/common-workflows.md` | 1 |
| `https://code.claude.com/docs/en/costs.md` | 1 |
| `https://code.claude.com/docs/en/env-vars.md` | 1 |
| `https://code.claude.com/docs/en/github-actions.md` | 1 |
| `https://code.claude.com/docs/en/gitlab-ci-cd` | 1 |
| `https://code.claude.com/docs/en/gitlab-ci-cdR` | 1 |
| `https://code.claude.com/docs/en/google-vertex-ai.md` | 1 |
| `https://code.claude.com/docs/en/hooks.md` | 1 |
| `https://code.claude.com/docs/en/interactive-mode.md` | 1 |
| `https://code.claude.com/docs/en/jetbrains.md` | 1 |
| `https://code.claude.com/docs/en/mcp.md` | 1 |
| `https://code.claude.com/docs/en/memory.md` | 1 |
| `https://code.claude.com/docs/en/microsoft-foundry.md` | 1 |
| `https://code.claude.com/docs/en/network-config.md` | 1 |
| `https://code.claude.com/docs/en/output-styles.md` | 1 |
| `https://code.claude.com/docs/en/permissions` | 1 |
| `https://code.claude.com/docs/en/permissions.md` | 1 |
| `https://code.claude.com/docs/en/plugins.md` | 1 |
| `https://code.claude.com/docs/en/sandboxing.md` | 1 |
| `https://code.claude.com/docs/en/sandboxing=` | 1 |
| `https://code.claude.com/docs/en/security.md` | 1 |
| `https://code.claude.com/docs/en/settings.md` | 1 |
| `https://code.claude.com/docs/en/skills.md` | 1 |
| `https://code.claude.com/docs/en/sub-agents.md` | 1 |
| `https://code.claude.com/docs/en/vs-code.md` | 1 |
| `https://downloads.claude.ai/claude-code-releases/` | 1 |
| `https://downloads.claude.ai/claude-code-releases/plugins/claude-plugins-official` | 1 |
| `https://downloads.claude.ai/claude-code-releases/plugins/claude-plugins-official%` | 1 |
| `https://platform.claude.com/settings/keys` | 1 |

## Session id regexes (4)

| value | hits |
|---|---|
| `^(?:session\|cse)_[A-Za-z0-9_-]+$` | 2 |
| `^(?:session\|cse)_[A-Za-z0-9_]+$` | 2 |
| `^(?:session\|cse)_
underWay
lastFailedAtMs
file:///$` | 1 |
| `^(?:session\|cse)_/,"")}function t9(e){return(e.startsWith("session_")\|\|e.startsWith("cse_"))&&IB(e)&&or(e)!==""}
export{JJr,Vr,Ph,IB,QJr,gu,sKt,cc,iKt,or,t9};
// @bun @bytecode
// Claude Code is a Beta product per Anthropic's Commercial Terms of Service.
// By using Claude Code, you agree that all code acceptance or rejection decisions you make,
// and the associated conversations in context, constitute Feedback under Anthropic's Commercial Terms,
// and may be used to improve Anthropic's products, including training models.
// You are responsible for reviewing any code suggestions before use.
// (c) Anthropic PBC. All rights reserved. Use is subject to the Legal Agreements outlined here: https://code.claude.com/docs/en/legal-and-compliance.
// Version: 2.1.287
import{xA,De}from"/$` | 1 |
