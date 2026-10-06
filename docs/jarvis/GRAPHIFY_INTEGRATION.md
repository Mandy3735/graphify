# Graphify adapter

Graphify 0.9.77 is reused, not copied. The adapter offers health/index/update/
query/explain/path/impact over operator-registered project IDs. Models and HTTP
clients never select a host path. Scoped query and path helpers are upstream
internal extension points isolated to this adapter and covered with fixture tests.

Return graph identity, update time, source file/location, relation, confidence
(EXTRACTED/INFERRED/AMBIGUOUS/UNKNOWN), and explicit untrusted-data status.
Unknown confidence is not promoted to EXTRACTED. Preserve stored arc direction
through Graphify's loader. Impact analysis is structural evidence, not a proof
that a change is safe. Always inspect source, diff and tests.

Index/update use Graphify collect/extract/build-merge/export on an immutable local
snapshot; only local AST extraction occurs. Merge preserves existing semantic
contributions for surviving files. A JARVIS extraction manifest tracks removed
AST sources; graph output is written atomically to the bounded output directory.
No model API or generated HTML iframe is involved. Updates currently re-extract
the bounded code snapshot rather than optimizing incremental AST caching.

Workspace reads use descriptor-relative traversal with no-follow flags, block
sensitive/hidden files, reject dot-dot/absolute paths and cap bytes. Operator roots
must not include credentials. Graph output and manifest reads/writes receive
equivalent path checks. The snapshot reduces mutable-source race exposure.
