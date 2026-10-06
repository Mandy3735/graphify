# Personal memory — next milestone

Personal memory is not implemented in the foundation checkpoint. AgentRun messages
are durable execution records, not the personal memory database. Graphify's code
graph remains a separate subsystem. No memory search/write/delete API is claimed.

Phase 5 will introduce WORKING/EPISODIC/SEMANTIC/CANONICAL/PREFERENCE classes,
source provenance, structured namespaces, actor/visibility filters applied before
model context, a relevance/budget-aware ContextBuilder, and inspector APIs.
pgvector is optional retrieval acceleration, never the authority for canonical
state. GM_SECRET and player-private filters must precede retrieval/model input.
See the phase 5 acceptance criteria in JARVIS_PLAN.md.
