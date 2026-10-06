import asyncio
import json

import pytest

from jarvis.graph import GraphifyKnowledgeProvider
from jarvis.paths import PathDenied, safe_read, safe_write


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "fixture"
    root.mkdir()
    (root / "core.py").write_text("def compute(value):\n    return value + 1\n")
    (root / "app.py").write_text("from core import compute\ndef run():\n    return compute(2)\n")
    return root


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "/etc/passwd",
        "a/../../x",
        "a\\x",
        "a//b",
        ".env",
        ".git/config",
        "secrets.json",
        "private.key",
    ],
)
def test_workspace_denies_unsafe_paths(tmp_path, path):
    with pytest.raises(PathDenied):
        safe_read(tmp_path, path)


def test_symlink_file_and_parent_escape_denied(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret")
    (root / "escape.txt").symlink_to(outside)
    (root / "directory").symlink_to(tmp_path, target_is_directory=True)
    for path in ["escape.txt", "directory/outside.txt"]:
        with pytest.raises(PathDenied):
            safe_read(root, path)
    with pytest.raises(PathDenied):
        safe_write(root, "directory/new.txt", b"write")
    assert not (tmp_path / "new.txt").exists()


def test_bounded_regular_io(tmp_path):
    safe_write(tmp_path, "folder/source.txt", b"ordinary")
    assert safe_read(tmp_path, "folder/source.txt") == b"ordinary"
    with pytest.raises(PathDenied):
        safe_read(tmp_path, "folder/source.txt", limit=2)


async def test_graphify_fixture_index_query_explain_path_impact_update(project):
    provider = GraphifyKnowledgeProvider({"fixture": project})
    assert provider.health("fixture") == {"project_id": "fixture", "indexed": False}
    result = await provider.index_project("fixture")
    assert result["indexed"] and result["nodes"] > 2
    evidence = provider.explain("fixture", "core.py::compute")
    assert evidence["trust"] == "UNTRUSTED_DATA"
    assert any(n["source_file"] == "core.py" and n["source_location"] for n in evidence["nodes"])
    assert evidence["edges"]
    assert all(
        e["confidence"] in {"EXTRACTED", "INFERRED", "AMBIGUOUS", "UNKNOWN"}
        for e in evidence["edges"]
    )
    answer = provider.query("fixture", "compute", 500)
    assert "core.py" in answer["text"]
    path = provider.path("fixture", "app.py::run", "core.py::compute")
    assert "Shortest path" in path["text"]
    impact = provider.impact("fixture", "core.py::compute")
    assert impact["affected_count"] >= 1
    (project / "core.py").write_text("def replaced(value):\n    return value - 1\n")
    (project / "app.py").write_text(
        "from core import replaced\ndef run():\n    return replaced(2)\n"
    )
    await provider.update_project("fixture")
    graph = provider._load("fixture")
    assert any("replaced" in str(d.get("label")) for _, d in graph.nodes(data=True))
    assert not any(d.get("label") == "compute()" for _, d in graph.nodes(data=True))


async def test_graph_update_preserves_existing_semantic_evidence(project):
    provider = GraphifyKnowledgeProvider({"fixture": project})
    await provider.index_project("fixture")
    data = json.loads((project / "graphify-out/graph.json").read_text())
    data["nodes"].append(
        {
            "id": "semantic-lore",
            "label": "design rationale",
            "type": "concept",
            "source_file": "README.md",
            "source_location": "L1",
        }
    )
    safe_write(project, "graphify-out/graph.json", json.dumps(data).encode())
    await provider.update_project("fixture")
    assert "semantic-lore" in provider._load("fixture")


async def test_worker_has_no_inherited_credentials_and_skips_sensitive_sources(
    project, monkeypatch
):
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret-never-to-worker")
    monkeypatch.setenv("JARVIS_AUTH_TOKEN", "private-token")
    (project / ".env").write_text("private credential")
    (project / "secrets.json").write_text('{"secret":"private"}')
    seen = []
    original = asyncio.create_subprocess_exec

    async def capture(*args, **kwargs):
        seen.append(kwargs["env"])
        return await original(*args, **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", capture)
    provider = GraphifyKnowledgeProvider({"fixture": project})
    await provider.index_project("fixture")
    assert seen and set(seen[0]) == {"PATH", "LANG", "PYTHONHASHSEED"}
    assert "private" not in (project / "graphify-out/graph.json").read_text()


async def test_graph_output_symlink_and_unregistered_project_rejected(project, tmp_path):
    provider = GraphifyKnowledgeProvider({"fixture": project})
    with pytest.raises(PathDenied):
        provider.health("../other")
    (project / "graphify-out").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(PathDenied):
        await provider.index_project("fixture")
    assert not (tmp_path / "graph.json").exists()
