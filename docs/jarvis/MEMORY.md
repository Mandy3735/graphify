# Personal memory — phase 5

PostgreSQL is the record of personal memory; Graphify remains the code knowledge
store. AgentRun messages are execution/conversation history, not the memory
database. Apply the additive Alembic revision `0002` before starting this backend.
The migration does not alter foundation tables, approvals or append-only audit.

## Classes and lifecycle

| Class | Meaning | Inspector correction/deletion |
|---|---|---|
| WORKING | Current task/session data in `session:<id>` | Allowed; expires within the configured working-memory TTL |
| EPISODIC | Chronological meaningful event | Append-only through this inspector; add a subsequent event |
| SEMANTIC | Retrievable document/note/conversation knowledge | Allowed |
| CANONICAL | Owner-supplied structured state | Creation needs `memory.canonical_write`; correction/deletion needs a future domain workflow |
| PREFERENCE | Explicit inspectable personalization | Allowed |

Canonical memory records do not administer application capabilities, approvals,
campaigns, inventory, or Tutor mastery. Those domain services remain separate
milestones. A memory containing permission text never grants that permission.

Corrections use an expected revision and create a new linked record; the prior
record and its sources remain inspectable but leave retrieval. At most 32
revisions are permitted in one lineage. A shared PostgreSQL root lock plus an
atomic revision claim prevents competing edits and deletion from resurrecting a
record. Deleting an eligible lineage clears all its contents, structured data,
embeddings, source quotes/locators, and accepted proposal payloads. Tombstone IDs
and content-free audit events remain. Human deletion retries are idempotent.

Expiry excludes working memory from retrieval without extending its TTL on
correction. Expired records remain explicitly inspectable until deletion; no
background physical-purge worker is implemented.

## Provenance and authorization

Every record requires 1–8 sources with kind, locator and optional bounded quote.
Sources have IDs, timestamps, and a SHA-256 hash of the supplied quote (or content
when no quote is given). These are source assertions, not a claim that a URL was
fetched or that the assertion was independently verified. Locators are never
executed or fetched. Model-accepted notes receive `MODEL_PROPOSAL` provenance.

Namespaces are `personal`, `project:<id>`, `campaign:<id>`, or `session:<id>`.
Owner ID comes only from configured bearer identity. SQL predicates apply owner,
namespace, optional mode, visibility, expiry and supersession **before** reading
candidates or ranking. A second live check follows an embedding await, so a
concurrent deletion/correction/expiry cannot reuse a stale search result.

Visibility includes PRIVATE, PUBLIC, PARTY, PLAYER_PRIVATE, GM_SECRET, INFERRED,
RUMOR and RETIRED. All remain owner-scoped, including PUBLIC/PARTY; this checkpoint
does not implement campaign membership or cross-user sharing. GM_SECRET requires
both the trusted `memory.gm_secret` capability and GAME_MASTER mode. Selecting a
mode does not grant a capability. RETIRED never enters retrieval. Inspect/list/
export/history endpoints apply the same owner and visibility checks.

The backend still uses one configured bearer identity. Independent configured
actors are isolated in tests; this does not create multi-user login, party
membership, or the phase-8 campaign secrecy system.

## Retrieval and context

`JARVIS_EMBEDDING_PROVIDER=fake` is the offline default. Its stable hashed terms
and small test aliases exercise ranking; it does not claim production semantic
intelligence. Live embeddings use the official OpenAI SDK only when the operator
selects `openai` and an explicit available model/dimension configuration. Provider
failures are bounded and returned without SDK credentials or request contents.

Embedding vectors carry a provider/model/dimension key. Incompatible vectors are
not mixed; lexical retrieval remains available for older records. Candidates are
limited to the latest `JARVIS_MEMORY_CANDIDATES` authorized active rows (default
128, maximum 512). This bounds cost and work; it is not exhaustive search over
an arbitrarily large archive. Inspector list/export uses bounded cursor pages.

Ranking combines matched terms and cosine similarity. Context may additionally
include applicable preferences, current session state, recent episodic events,
and canonical state for the current project/campaign. Every hit explains its
retrieval reason and retains its namespace, visibility and source references.

ContextBuilder takes trusted actor/capabilities, mode, current project/campaign/
session, request and budget. It inserts only fitting relevant records as marked
**untrusted user data**, preserving the actual objective. UTF-8 bytes plus message
framing provide a conservative token upper bound independent of model tokenizer.
The whole-context token cap includes tool schemas as well as message framing,
tool arguments/results and memory. The character cap bounds message text;
a request may lower, but never raise, the server budget. Oversized memory is
omitted with a count in run metadata; required request/tool context exceeding the
budget fails the run.

Context is rebuilt before each model call. Stored memory-search tool results are
refiltered against current live records, including after an embedding wait.
Auto-retrieved memory text is not copied into AgentRun messages. Run metadata
records memory/source IDs, retrieval reasons, budget and omission counts.
Graphify evidence remains a separate typed tool result; Engineer project requests
still query Graphify before the model.

Deleting memory does not erase earlier user messages, model answers, or historical
tool execution transcripts. Their retention/export is a separate conversation
workflow. Such historical memory-search results are revalidated before entering
any subsequent model context. Audit retains identifiers, not deleted facts.

## Inspector and proposal APIs

All endpoints below require bearer authentication and current server capabilities.
`memory.read` grants search/inspect/export. `memory.write` grants eligible direct
user writes and proposal decisions. `memory.propose` allows inactive proposals.

| Endpoint | Behavior |
|---|---|
| GET `/api/memories` | Cursor page, namespace/mode selection, optional history |
| GET `/api/memories/{id}` | Sources, scope, lifecycle and edit/delete eligibility |
| POST `/api/memories` | Explicit user write; provenance required |
| POST `/api/memories/search` | Relevant authorized hits with retrieval reasons |
| PATCH `/api/memories/{id}` | Expected-revision correction; returns replacement ID |
| DELETE `/api/memories/{id}` | Purges eligible lineage, returns 204 |
| GET `/api/memories/export` | Scoped paginated JSON with sources, not a database dump |
| GET `/api/memory-proposals` | Scoped inactive proposals |
| POST `/api/memory-proposals/{id}/accept` | Atomic one-use human acceptance |
| POST `/api/memory-proposals/{id}/reject` | Human rejection, no active memory |

For non-personal inspect/correct/delete/proposal decisions, pass the matching
`namespace` query parameter and applicable `mode`. Memory-search bodies include
namespace/mode; chat accepts project_id/campaign_id/session_id to choose context.
Neither accepts an actor ID or capability grant from the caller.

Model tools are `memory.search` and `memory.propose_write`, bound to the actual
run's trusted actor, mode and namespaces. The model cannot select another
namespace or impersonate a GM role through arguments. Proposed memory is never
active until an authenticated human accepts it. Models cannot propose canonical
or GM-secret records. There is no model tool to accept, correct or delete memory.

The interactive API inspector is available through `/docs`. A dedicated memory
screen and the Command Center frontend remain phase 9.

## Optional pgvector

Set `JARVIS_MEMORY_PGVECTOR=true` only on PostgreSQL with the `vector` extension
explicitly installed by an administrator. Startup fails clearly if it is missing.
Schema migration `0002` never silently installs extensions. Embeddings stay in the
same durable JSON field; bounded, already-authorized candidate IDs are ranked
using pgvector's cosine operator. This is optional vector computation, not an
unbounded ANN index. No additional Python package is required.

See LOCAL_DEVELOPMENT.md for opt-in setup and both database test configurations.
