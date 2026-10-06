import asyncio
import fcntl
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Protocol

from jarvis.paths import PathDenied, parent_fd, parts, safe_read, safe_write

GRAPH = "graphify-out/graph.json"
MANIFEST = "graphify-out/jarvis-index.json"
GRAPH_LIMIT = 32 * 1024 * 1024


class GraphKnowledgeProvider(Protocol):
    async def index_project(self, project_id: str) -> dict[str, Any]: ...
    async def update_project(self, project_id: str) -> dict[str, Any]: ...
    def query(self, project_id: str, question: str, budget: int = 1200) -> dict[str, Any]: ...
    def explain(self, project_id: str, node: str) -> dict[str, Any]: ...
    def path(self, project_id: str, source: str, target: str) -> dict[str, Any]: ...
    def impact(self, project_id: str, node: str, depth: int = 2) -> dict[str, Any]: ...
    def health(self, project_id: str) -> dict[str, Any]: ...


class GraphifyKnowledgeProvider:
    def __init__(self, projects: dict[str, Path], timeout: float = 60):
        self.projects = projects
        self.timeout = timeout

    def root(self, project_id: str) -> Path:
        if project_id not in self.projects:
            raise PathDenied("Project is not registered by the operator")
        return self.projects[project_id]

    def _load(self, project_id: str):
        from graphify.paths import load_node_link_graph

        data = json.loads(safe_read(self.root(project_id), GRAPH, limit=GRAPH_LIMIT))
        if len(data.get("nodes", [])) > 50000 or len(data.get("links", [])) > 150000:
            raise ValueError("Graph exceeds prototype resource budget")
        return load_node_link_graph(data)

    def health(self, project_id: str) -> dict[str, Any]:
        root = self.root(project_id)
        try:
            graph = self._load(project_id)
            stamp = datetime.fromtimestamp((root / GRAPH).stat().st_mtime, UTC).isoformat()
            return {
                "project_id": project_id,
                "indexed": True,
                "nodes": len(graph),
                "edges": graph.number_of_edges(),
                "updated_at": stamp,
            }
        except FileNotFoundError:
            return {"project_id": project_id, "indexed": False}

    def _evidence(self, graph, nodes) -> dict[str, Any]:
        chosen = set(nodes)
        return {
            "nodes": [
                {
                    "id": str(n),
                    "label": graph.nodes[n].get("label", str(n)),
                    "source_file": graph.nodes[n].get("source_file"),
                    "source_location": graph.nodes[n].get("source_location"),
                }
                for n in sorted(chosen)
            ],
            "edges": [
                {
                    "source": d.get("_src", u),
                    "target": d.get("_tgt", v),
                    "relation": d.get("relation", "related"),
                    "confidence": d.get("confidence", "UNKNOWN"),
                    "source_file": d.get("source_file"),
                    "source_location": d.get("source_location"),
                }
                for u, v, d in graph.edges(data=True)
                if u in chosen and v in chosen
            ][:128],
            "trust": "UNTRUSTED_DATA",
        }

    def query(self, project_id: str, question: str, budget: int = 1200) -> dict[str, Any]:
        from graphify.serve import _pick_seeds, _query_graph_text, _query_terms, _score_nodes

        graph = self._load(project_id)
        seeds = _pick_seeds(_score_nodes(graph, _query_terms(question)))
        evidence = self._evidence(graph, seeds[:12])
        text = _query_graph_text(graph, question, depth=2, token_budget=budget, graph_path=GRAPH)
        return {"project_id": project_id, "text": text[: budget * 6], **evidence}

    def _node(self, graph, name: str) -> str:
        from graphify.serve import _resolve_single_node

        node, warning = _resolve_single_node(graph, name)
        if not node:
            raise ValueError((warning or "Node not found")[:1000])
        return node

    def explain(self, project_id: str, node: str) -> dict[str, Any]:
        graph = self._load(project_id)
        seed = self._node(graph, node)
        neighbors = sorted(graph.neighbors(seed))[:30]
        return {"project_id": project_id, "node": seed, **self._evidence(graph, [seed, *neighbors])}

    def path(self, project_id: str, source: str, target: str) -> dict[str, Any]:
        from graphify.serve import _shortest_path_text

        graph = self._load(project_id)
        return {
            "project_id": project_id,
            "trust": "UNTRUSTED_DATA",
            "text": _shortest_path_text(graph, {"source": source, "target": target, "max_hops": 8})[
                :12000
            ],
        }

    def impact(self, project_id: str, node: str, depth: int = 2) -> dict[str, Any]:
        from graphify.affected import affected_nodes

        graph = self._load(project_id)
        seed = self._node(graph, node)
        hits = affected_nodes(graph, seed, depth=depth)
        return {
            "project_id": project_id,
            "affected_count": len(hits),
            **self._evidence(graph, [seed, *(h.node_id for h in hits[:40])]),
        }

    async def index_project(self, project_id: str) -> dict[str, Any]:
        return await self.update_project(project_id)

    async def update_project(self, project_id: str) -> dict[str, Any]:
        from graphify.extract import collect_files

        root = self.root(project_id)
        with parent_fd(root, "graphify-out/jarvis-index.lock", internal=True, create=True) as (
            fd,
            name,
        ):
            lock = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=fd)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with TemporaryDirectory(prefix="jarvis-graph-") as temporary:
                stage = Path(temporary)
                snapshot = stage / "source"
                snapshot.mkdir()
                files = await asyncio.to_thread(collect_files, root, root=root)
                if len(files) > 1500:
                    raise ValueError("Project exceeds prototype source file budget")
                sources: list[str] = []
                total = 0
                for file in files:
                    relative = file.relative_to(root).as_posix()
                    try:
                        parts(relative)
                    except PathDenied:
                        continue
                    data = await asyncio.to_thread(safe_read, root, relative, limit=2 * 1024 * 1024)
                    total += len(data)
                    if total > 32 * 1024 * 1024:
                        raise ValueError("Project exceeds prototype source byte budget")
                    destination = snapshot / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(data)
                    sources.append(relative)
                graph = stage / "graph.json"
                try:
                    graph.write_bytes(safe_read(root, GRAPH, limit=GRAPH_LIMIT))
                except FileNotFoundError:
                    pass
                try:
                    old = json.loads(safe_read(root, MANIFEST)).get("sources", [])
                except FileNotFoundError:
                    old = []
                metadata = {"sources": sources, "deleted": sorted(set(old) - set(sources))}
                manifest = stage / "manifest.json"
                manifest.write_text(json.dumps(metadata))
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "jarvis.graph_worker",
                    str(snapshot),
                    str(graph),
                    str(manifest),
                    env={
                        "PATH": str(Path(sys.executable).parent),
                        "LANG": "C.UTF-8",
                        "PYTHONHASHSEED": "0",
                    },
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    await asyncio.wait_for(process.wait(), timeout=self.timeout)
                except BaseException:
                    if process.returncode is None:
                        process.kill()
                        await process.wait()
                    raise
                if process.returncode:
                    raise ValueError("Graphify parser failed; prior graph retained")
                if graph.stat().st_size > GRAPH_LIMIT:
                    raise ValueError("Generated graph exceeds resource budget")
                safe_write(root, GRAPH, graph.read_bytes())
                safe_write(root, MANIFEST, json.dumps(metadata).encode())
            return self.health(project_id)
        finally:
            os.close(lock)
