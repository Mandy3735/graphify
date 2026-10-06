# JARVIS threat model (phases 0–5 checkpoint)

Existing Graphify controls remain documented in SECURITY.md. This document
describes the added persistent application and must not be mistaken for future
features being implemented.

| Threat / boundary | Implemented contract or required future mitigation |
|---|---|
| Unauthenticated HTTP → authority | Mandatory server token, constant-time check; owner-scoped rows; loopback default |
| Model/retrieval → capability | Strict schemas/registry and deterministic server-side grants; no authority derived from text |
| Approval spoof/replay/mutation | Exact operation digest/nonce/expiry; actor/run binding; atomic one-use consume; audited |
| Repository → host filesystem | Operator registrations; descriptor-relative no-follow reads; safe staging and bounded output writes |
| Code → execution / shell escape | No arbitrary execution tool; isolated parser subprocess only. Engineer sandbox pending |
| Worker → credentials | Minimal constructed environment, no inherited API/database/token secrets |
| Graph → answer | Source locations/confidence retained; content labeled untrusted; cannot grant permissions |
| Tool output → UI/model | Capped validated output; tool results data; future UI must use text/escaped rendering |
| Model outage/retirement/downgrade | Configurable IDs; typed errors; no auth fallback; explicit non-high-stakes fallback policy; visible metadata |
| Excessive cost / loops | Run/model/tool deadlines, fixed max tool calls, bounded model outputs; production request rate limits pending |
| Crash → duplicate effect | Durable transitions; no replay of executing runs after restart; external idempotency integration pending |
| Audit rewrite | No API/tool mutation; PostgreSQL append-only trigger; privileged DB administrators remain trusted |
| Poisoned personal memory / cross-owner leaks | SQL owner/namespace/mode/visibility/lifecycle filters before retrieval; untrusted data context; no permission grants; human acceptance for model proposals |
| Stale/deleted memory → model context | Recheck live records after embedding awaits; rebuild context and refilter historical memory tools before each model call; purge eligible revision lineages |
| GM secrets / voice spoof / device authority | GM/voice/device workflows pending; no placeholder claim of enforcement |
| OAuth/MCP/plugins/supply chain | No integration authority enabled; dependency lock/checks; future integration-specific review |
| Proactive automation | Watchers pending; no unrestricted polling or self-spawning agents |

Trusted: operator configuration, application source, configured bearer holder,
migration/admin DB role. Untrusted: model responses, source files/comments/README,
graph text, remote integration responses. Server secrets never enter model input
or worker environment. Production needs TLS, secret management, a non-owner DB
role, token rotation, identity/session hardening and admission/rate limits.

Phase 5 keeps PUBLIC/PARTY owner-scoped. GM-secret personal memory needs trusted
capability plus GM mode; campaign membership/sharing remains phase 8. Canonical
memory cannot edit application authorization state. Source locators are asserted
data and never fetched/executed. Inspector exports are scoped bounded pages.
Conversation/model/tool transcripts have separate retention from eligible memory
deletion; historical memory search data is revalidated before future model input.
