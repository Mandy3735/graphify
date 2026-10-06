# Graphify baseline — 2026-10-05

Repository: `/workspace/graphify`; original branch `work`; clean tracked tree.
Commit: `5c7b84792f453582676548185aaec3824d51dfe2` (release 0.9.77).
Working transformation branch: `jarvis/foundation`.
License: Apache-2.0 with LICENSE-MIT and NOTICE preserved.

## Reconnaissance

Read AGENTS.md, ARCHITECTURE.md, SECURITY.md, README setup/interfaces,
pyproject.toml, CI/pre-commit settings, fixtures/test layout, CLI dispatch,
MCP server/query internals and bundled Codex skill guidance. No installed skill
was found in the workspace's agent directories. AGENTS.md supplies CLI guidance.

Graphify is a Python library/CLI with optional MCP/HTTP. Pipeline:
detect → extract → build → cluster → analyze → report/export. Tree-sitter code
extraction is deterministic; semantic extraction is a separate optional model
boundary. The CLI includes extract/update/query/path/explain, export, ingest,
watch, providers, global graphs, skill/hook installation and MCP serving.
Entry points: graphify.__main__:main and graphify.serve:_main.

Dependency management: root pyproject.toml + committed uv.lock; existing .venv.
CI tests Python 3.10/3.12/3.13/3.14, checks skill generation, scans security.
Ruff uses conservative fatal-error selectors; Pyright basic mode covers graphify
and tests; repository-wide formatter is not clean at baseline.

Existing graphify-out contained AST caches but no graph.json/report/wiki.
Initial `graphify query` failed with missing graph.json. `graphify update .`
built an AST graph: 18,678 nodes, 38,010 edges, 1,052 communities. It warned
about missing optional grammars and one Luau fixture syntax error. Query/explain
then worked. Broad query matched 4,833 nodes and truncated; a scoped explanation
of graphify/serve.py::_query_graph_text linked to L1361 and the CLI/tests.

Security: upstream URL/SSRF validation, fetch size/time caps, constrained MCP graph
paths, HTML escaping, untrusted-source delimiters for semantic extraction, no
source execution and no shell=True. Persistent JARVIS adds identity, durable
authority, model/tool execution and audit boundaries; these are not supplied by
Graphify's local-tool security model.

## Commands and results

Executed before JARVIS source changes:

- `.venv/bin/python -m pytest tests/ -q` — interrupted after 354.49 s during
  installer resolution (5,659 passed, 102 skipped, 28 failed at interruption).
- `PATH=/workspace/graphify/.venv/bin:/usr/local/bin:/usr/bin:/bin .venv/bin/python -m pytest tests/ -q`
  — complete offline baseline: **6,439 passed, 108 skipped, 40 failed**, 103.15 s.
  Optional Erlang/R/Solidity/VB.NET/OpenAI dependencies were missing; other failures
  involved ignore/VCS behavior, socket/filesystem restrictions and DNS validation.
- `.venv/bin/ruff check .` — passed.
- `.venv/bin/ruff format --check .` — failed: 430 files would change, 23 formatted.
- `.venv/bin/pyright` — failed: 881 errors/149 warnings, including interpreter-resolution problems.
- `.venv/bin/python -m pyright --pythonpath /workspace/graphify/.venv/bin/python`
  — failed: 880 errors/149 warnings. Existing issues will be preserved, not masked.
- `.venv/bin/graphify --help`, `query`, `explain`, `update .` as described above.

See JARVIS_PROGRESS.md and the final engineering report for final test evidence.
Raw baseline logs live under ignored `work/`.

After installing missing optional test dependencies (environment only), regression
had 6,470 passed, 108 skipped and 9 failed. The remaining 9 were all in the baseline
failure list. A Pyright config explicitly naming the existing venv reported 639
errors/4 warnings; no upstream source or type-check setting was changed to hide them.

## Intended reuse and changes

Reuse extraction/build/export/path loading/scoped querying behind the adapter.
Do not modify Graphify modules, tests, fixtures, CLI, MCP, generated skills,
packaging, lock or existing CI. Unavoidable core modifications: none currently.
