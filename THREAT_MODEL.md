# JARVIS threat model (phases 0–10 checkpoint)

Existing Graphify controls remain documented in SECURITY.md. This document
describes the added persistent application and must not be mistaken for future
features being implemented.

| Threat / boundary | Implemented contract or required future mitigation |
|---|---|
| Unauthenticated HTTP → authority | Mandatory server token, constant-time check; owner-scoped rows; loopback default |
| Model/retrieval → capability | Strict schemas/registry and deterministic server-side grants; no authority derived from text |
| Approval spoof/replay/mutation | Exact operation digest/nonce/expiry; actor/run binding; atomic one-use consume; audited |
| Repository → host filesystem | Operator registrations; descriptor-relative no-follow reads; safe staging and bounded output writes |
| Code → execution / shell escape | Opt-in kernel-verified Bubblewrap, offline read-only source/runtime, UID/capability drop, no-new-privileges, disabled nested user namespaces; no host fallback |
| Worker → credentials | Constructed environment; no host home/Git/config/secret mounts; eligible tracked plain-file snapshots only |
| Project Git hooks/filters → host execution | Original Git calls only inspect HEAD/tracked names; no original checkout/add/diff/filter execution. Worktree is created in a fresh sanitized private repository |
| Sandbox → runaway resources | Wall/CPU/address-space/process/file/descriptor/output/tmpfs bounds; terminate process sessions/PID namespaces on cancellation; aggregate cgroup memory quotas remain future hardening |
| Artifact → another actor / disk growth | Actor/run provenance and owner checks; private directory; bounded reports and 128-job admission cap; operator retention/orphan cleanup |
| Graph → answer | Source locations/confidence retained; content labeled untrusted; cannot grant permissions |
| Tool output → UI/model | Capped validated output; tool results data; Phase 9 UI uses literal bounded text |
| Model outage/retirement/downgrade | Configurable IDs; typed errors; no auth fallback; explicit non-high-stakes fallback policy; visible metadata |
| Excessive cost / loops | Run/model/tool deadlines, fixed max tool calls, bounded model outputs; production request rate limits pending |
| Crash → duplicate effect | Durable transitions; no replay of executing runs after restart; external idempotency integration pending |
| Audit rewrite | No API/tool mutation; PostgreSQL append-only trigger; privileged DB administrators remain trusted |
| Poisoned personal memory / cross-owner leaks | SQL owner/namespace/mode/visibility/lifecycle filters before retrieval; untrusted data context; no permission grants; human acceptance for model proposals |
| Stale/deleted memory → model context | Recheck live records after embedding awaits; rebuild context and refilter historical memory tools before each model call; purge eligible revision lineages |
| Generated lesson/model answer → false mastery | No model attempt/mastery/review tool; server-stamped HUMAN_API attempts; deterministic grading; mastery retains exact attempt IDs |
| Tutor source/prompt injection → authority | Source ownership validated before citation; content labeled untrusted; run/objective/capability bound before tool execution |
| Duplicate/racing attempts → duplicate mastery | Objective row lock, unique submission/evidence/review constraints, idempotent exact replay and changed-answer conflict |
| Premature spaced review → false retention | Review completion requires a correct human attempt made at or after the task due time |
| GM secret / private player leak | Explicit membership plus SQL visibility predicates before limits/model input; adversarial player-context tests include filter-after-limit |
| Creative prose/transcript → canonical state | Structured proposal tables are non-canonical; authenticated GM role/capability and row-locked decision transaction required |
| Forged membership/mode/campaign | Actor comes from authentication/configuration; service membership lookup and tool run campaign/session binding precede reads/effects |
| PC authority theft / delegation replay | Human by default; controller-only reporting/delegation; delegation expires and is atomically one-use; nonce TTL and all meaningful request fields must replay exactly |
| Secret entity ID → dice side channel | Subject visibility is independently checked before roll authority; unauthorized/retired UUIDs return the same not-found boundary |
| Fabricated or abusive randomness | Strict bounded parser and plausible human totals; injected system/seeded RNG; rolls retain actor, reason, visibility, raw/kept/discarded dice, total, authority and entropy reference |
| Secret transcript injection | Transcript visibility filtered before scene limit; players cannot author GM-secret or another player's private line; transcripts remain untrusted/non-canonical |
| Voice spoof / device authority | Explicit opt-in and reviewed untrusted transcripts; ordinary policy-controlled runs; no voice authentication or human-decision authority |
| OAuth/MCP/plugins/supply chain | No integration authority enabled; dependency lock/checks; future integration-specific review |
| Proactive automation | Watchers pending; no unrestricted polling or self-spawning agents |

Trusted: operator configuration, application source, configured bearer holder,
migration/admin DB role. Untrusted: model responses, source files/comments/README,
graph text, remote integration responses. Server secrets never enter model input
or worker environment. Production needs TLS, secret management, a non-owner DB
role, token rotation, identity/session hardening and admission/rate limits.

Phase 5 personal memory remains owner-scoped, including PUBLIC/PARTY. GM-secret
personal memory needs trusted capability plus GM mode. Phase 8 campaign state uses
separate explicit membership and sharing rather than changing personal-memory
ownership. Canonical
memory cannot edit application authorization state. Source locators are asserted
data and never fetched/executed. Inspector exports are scoped bounded pages.
Conversation/model/tool transcripts have separate retention from eligible memory
deletion; historical memory search data is revalidated before future model input.

Engineer execution currently supports system-Python standard-library commands on
Linux hosts permitting the required namespace/mount operations. Startup probes
real isolation; unsupported hosts retain text/memory and register no execution
tools. Shared-kernel risks, aggregate cgroup quotas and multi-worker support remain
production-hardening work. See docs/jarvis/ENGINEER.md for precise guarantees.

Tutor uses normalized exact-answer matching. Accepted-answer hashes reduce casual
disclosure but are not secrets against an offline low-entropy dictionary attack;
database administrators remain trusted. Semantic/open-ended grading, production
learner identity and notification delivery remain future work. See TUTOR.md.

Game Master membership is application-level, not production account/session
identity. The default rules plugin is system-neutral. Scene relevance uses bounded
current campaign/session candidates rather than semantic ranking, and transcripts
have no automated recap pipeline yet. Database administrators remain trusted.
See GAME_MASTER.md.

## Phase 9 browser boundary

Untrusted API/model/graph/memory/campaign text is rendered literally with bounds;
no HTML/Markdown execution, external links or iframe graph is enabled. Bearer
credentials are held only in tab memory, cleared/aborted on sign-out, navigation
away or 401; old-client responses cannot act on a new identity. Scoped UI remounts
and obsolete-response guards separate modes, campaigns, sessions and namespaces.
Private root content is hidden on pagehide and persisted history reloads.

The same-origin host adds restrictive CSP, no-store/no-referrer/nosniff/frame
protection and disabled device permissions. A generated finite service-worker
allowlist caches only public application assets, never API data, authenticated
requests, writes, query URLs or other origins. Offline offers an unauthenticated
shell and queues no effects. Session-list reads require campaign membership;
proposal-history reads additionally require GM role before returning changes.
Browser E2E checks identity changes and GM-secret exclusion; authority remains in
existing server policy/services. Session titles are campaign-visible metadata and
must not be used as a secret field. Production account/session/TLS hardening and
optional voice still remain later work.

## Phase 10 audio boundary

Only explicit live opt-in enables microphone=(self); camera/geolocation stay denied.
SDP is bounded/audio-only and SDK credentials remain server-held. Realtime sees no
backend history/GM state/tools and cannot invoke application APIs. Transcript events
are bounded data, reviewed before ordinary run submission; all role/policy/approval
checks remain server-authoritative. Speech loads only an owned completed result.
Audio/session credentials are never stored/cached; raw audio is not persisted.

Immediate local track/peer/audio cleanup covers stop, sign-out, background/offline,
timeouts and stale permission/handshake responses. Remote hangup is bounded best
effort; failures are audited distinctly, and process crashes/outages can leave remote
work temporarily alive. Voice transport has one-operation/session admission, 30/hour
requests, bounded SDK deadlines/audio/text/session sizes and no retries. Provider
data-channel mutation never grants backend authority; stronger provider-level cost
quotas and crash reconciliation remain production work. See docs/jarvis/VOICE.md.

## Phase 11 enforced boundaries

Ingress applies authenticated/global/observed-peer rate, concurrency, slow-body and
wire-byte limits before parser/audit/DB/provider work. Caller-forwarded headers do not
choose peer identity or HTTPS. Production requires an exact HTTPS origin, strong
single-principal bearer and a restricted non-owner PostgreSQL role; developer API docs
are unavailable. Runtime role cannot alter audit/migration schema, create tables or
inherit privileged owners. An application advisory lease rejects another process;
lease loss disables API work and invokes shutdown. ASGI failures omit private exception
parameters; resource cleanup still runs after startup/shutdown errors.

Live official providers reserve configured estimates transactionally before calls;
usage is settled once, uncertainty remains charged and restart cannot reset UTC-day
admission. Estimates are not provider invoice guarantees. Live microphone is disabled
in production because remote data-channel settings cannot enforce a generation-cost
ceiling. Known voice IDs are journaled for stop recovery; unknown creation requires
explicit human reconciliation and no automatic replay. No human-only decision,
capability, canonical state or personal/campaign visibility boundary is weakened.

Provider-side billing limits, operational TLS/backups/monitoring, multi-user identity,
HA, retention and full Phase 12 acceptance remain out of scope. The new TLS/role
files are reviewed templates, not deployed infrastructure. See HARDENING.md.
