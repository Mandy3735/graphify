# Preserved upstream boundary

Upstream Graphify is `graphify/`, `tests/`, `tools/skillgen/`, `scripts/`, generated
skills, its CLI/MCP entrypoints, root pyproject/uv.lock, licenses, and existing CI.
Do not copy or rename its implementation. Existing tests are a regression boundary.

JARVIS lives in `apps/jarvis/` and `docs/jarvis/`, plus JARVIS planning/review/threat
documents and one separate CI workflow. Root documentation gets additive links.
The empty adjacent My-JARVIS-AI- repository is not the upstream Graphify codebase;
it is not rewritten or used to fork a duplicate implementation.

Reuse `extract.collect_files/extract`, `build.build_from_json`, `export.to_json`,
`paths.load_node_link_graph` and Graphify's scoped query/path helpers. The latter
are internal APIs: isolate their imports inside the adapter and pin/test against
Graphify 0.9.77. No changes to upstream modules are currently necessary.

Graphify has module-level extraction context. Serialize index/update inside an
isolated worker process rather than concurrently mutating extraction context in
the application process. Keep source_file/source_location and per-edge confidence;
use the upstream direction-aware loader, not raw NetworkX node_link_graph.

Generated `graphify-out/` stays local/ignored. Run `graphify update .` after source
changes; graph data assists navigation but never validates its own correctness.
JARVIS application memory and structured state remain separate from code graphs.
