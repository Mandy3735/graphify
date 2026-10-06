"""AST parser worker; inputs are safe snapshots, never executable project code."""

import json
import sys
from pathlib import Path


def main() -> None:
    from graphify.build import build_merge
    from graphify.export import to_json
    from graphify.extract import collect_files, extract

    snapshot, graph, metadata = (Path(p) for p in sys.argv[1:])
    manifest = json.loads(metadata.read_text())
    files = collect_files(snapshot, root=snapshot)
    extraction = extract(files, root=snapshot, parallel=False)
    merged = build_merge(
        [extraction],
        graph,
        root=snapshot,
        ast_sources=manifest["sources"],
        prune_sources=manifest["deleted"],
    )
    if not merged.number_of_nodes():
        raise ValueError("Empty extraction cannot replace a graph")
    # Community IDs are presentation hints; full clustering is an upstream CLI operation.
    to_json(merged, {}, str(graph), force=True)


if __name__ == "__main__":
    main()
