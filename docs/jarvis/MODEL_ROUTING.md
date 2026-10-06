# Model routing

Model IDs occur only in Settings defaults and environment examples. The router
selects primary reasoning or configured utility; tools cannot select model IDs.
OpenAIModelProvider uses the official AsyncOpenAI Responses SDK, with no SDK
automatic retries, bounded output, no remote response storage, safe tool history
translation and streaming/error/cancellation handling. Provider objects do not
escape into the domain layer. FakeModelProvider requires no paid services.

Fallback requires server configuration plus explicit request consent and is denied
for high-stakes runs. Authentication/configuration errors never trigger fallback.
Unavailable models, rate limiting and selected transient connection/server/time
errors may fall back; selection/usage/estimated configured cost and successful
fallback attempts are visible in run metadata and fallback audit events.

Function proposals are strict domain data. The model never executes tools or
controls capabilities. Exactly one tool proposal per response is supported;
parallel calls are disabled. Tool-call count, run/context/output/time budgets are
bounded. A provider failure fails the run; no tool effect is retried by the model
gateway. Production quotas and integration-specific idempotency are future work.

Voice and embeddings have reserved model configuration fields but no live
implementation at this checkpoint. A missing live key does not affect fake mode
startup. When OpenAI is selected without credentials, runs fail with a safe public
configuration error; no secret-bearing provider exception is exposed.
