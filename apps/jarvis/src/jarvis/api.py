import asyncio
import json
import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy import select, text

from jarvis.config import Settings
from jarvis.db import AgentRun, AgentStep, ApprovalRequest, AuditEvent, Database, audit
from jarvis.domain import TERMINAL, ChatRequest, Mode, StrictModel, ToolProposal
from jarvis.embeddings import EmbeddingProvider, embedding_provider
from jarvis.engine import Conflict, Engine
from jarvis.engineer import EngineerService
from jarvis.engineer_schema import ChangeRequest
from jarvis.engineer_tools import register_engineer_tools
from jarvis.graph import GraphifyKnowledgeProvider
from jarvis.memory import MemoryConflict, MemoryDenied, MemoryService
from jarvis.memory_api import memory_router
from jarvis.memory_tools import register_memory_tools
from jarvis.models import FakeModelProvider, ModelRouter, OpenAIModelProvider, ProviderFailure
from jarvis.sandbox import SandboxUnavailable
from jarvis.tools import ToolRegistry, graph_tools
from jarvis.tutor import TutorConflict, TutorDenied, TutorService
from jarvis.tutor_api import tutor_router
from jarvis.tutor_tools import register_tutor_tools


class QueryBody(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    budget: int = Field(default=1200, ge=100, le=2500)


class PathBody(StrictModel):
    source: str = Field(min_length=1, max_length=200)
    target: str = Field(min_length=1, max_length=200)


def run_json(run: AgentRun) -> dict:
    return {
        "id": run.id,
        "mode": run.mode,
        "state": run.state,
        "objective": run.request["message"],
        "result": run.result,
        "error": run.error,
        "metadata": run.metadata_json,
        "pending_tool": run.pending,
        "tool_count": run.tool_count,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
    }


def create_app(
    settings: Settings | None = None,
    provider=None,
    registry: ToolRegistry | None = None,
    embeddings: EmbeddingProvider | None = None,
):
    # BaseSettings obtains required fields from environment/.env at runtime.
    cfg = settings or Settings()  # pyright: ignore[reportCallIssue]
    db = Database(cfg.database_url.get_secret_value())
    graph = GraphifyKnowledgeProvider(cfg.project_roots, cfg.tool_timeout)
    provider = provider or (
        FakeModelProvider() if cfg.provider == "fake" else OpenAIModelProvider(cfg)
    )
    memory = MemoryService(db, cfg, embeddings or embedding_provider(cfg))
    tutor = TutorService(db)
    engineer = EngineerService(cfg, graph) if cfg.engineer_enabled else None
    default_registry = registry is None
    if registry is None:
        registry = graph_tools(graph)
        register_memory_tools(registry, memory)
        register_tutor_tools(registry, tutor)
    engine = Engine(cfg, db, ModelRouter(cfg, provider), registry, memory)

    @asynccontextmanager
    async def lifespan(app):
        # Requires an explicitly migrated database. Recovery never replays effects.
        await memory.check_backend()
        if engineer is not None and default_registry:
            try:
                await engineer.check_backend()
            except SandboxUnavailable:
                # Text/memory remain available; no execution tools are registered.
                pass
            else:
                register_engineer_tools(registry, engineer)
        await engine.recover()
        yield
        await engine.close()
        if isinstance(provider, OpenAIModelProvider):
            await provider.close()
        await db.dispose()

    app = FastAPI(title="JARVIS", version="0.4.0", lifespan=lifespan)
    app.state.engine, app.state.database, app.state.graph = engine, db, graph
    app.state.memory = memory
    app.state.tutor = tutor
    app.state.engineer = engineer

    async def authenticate(authorization: Annotated[str | None, Header()] = None):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Bearer authentication required")
        supplied = authorization[7:].encode()
        expected = cfg.auth_token.get_secret_value().encode()
        if not secrets.compare_digest(supplied, expected):
            raise HTTPException(401, "Invalid bearer token")
        async with db.sessions.begin() as session:
            audit(session, engine.actor.id, "authentication.accepted", {})

    auth = [Depends(authenticate)]
    app.include_router(memory_router(memory, engine.actor, auth))
    app.include_router(tutor_router(tutor, engine.actor, auth))

    @app.exception_handler(MemoryDenied)
    async def memory_denied(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(MemoryConflict)
    async def memory_conflict(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(TutorDenied)
    async def tutor_denied(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=403, content={"detail": str(exc)})

    @app.exception_handler(TutorConflict)
    async def tutor_conflict(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ProviderFailure)
    async def provider_unavailable(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"detail": "Embedding provider unavailable"})

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=404, content={"detail": "Resource not found"})

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.get("/health")
    async def health():
        try:
            async with db.sessions() as session:
                await session.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception:
            raise HTTPException(503, "Database unavailable") from None

    async def admit():
        if len(engine.tasks) >= 4:
            raise HTTPException(429, "Concurrent run budget reached")

    @app.post("/api/chat", status_code=202, dependencies=auth)
    async def chat(request: ChatRequest):
        await admit()
        return {"run_id": await engine.create(request)}

    @app.get("/api/engineer/status", dependencies=auth)
    async def engineer_status():
        return {
            "configured": cfg.engineer_enabled,
            "available": engineer is not None and engineer.sandbox.ready,
            "runtime": "Linux Bubblewrap, system Python standard library",
            "host_execution_fallback": False,
        }

    @app.post("/api/engineer/changes", status_code=202, dependencies=auth)
    async def engineering_change(request: ChangeRequest):
        await admit()
        if engineer is None or not engineer.sandbox.ready:
            raise HTTPException(503, "Verified Engineer sandbox unavailable")
        return {
            "run_id": await engine.create(
                ChatRequest(
                    message=request.objective, mode=Mode.ENGINEER, project_id=request.project_id
                ),
                ToolProposal(name="engineer.change", arguments=request.model_dump(mode="json")),
            )
        }

    @app.get("/api/engineer/artifacts/{artifact_id}", dependencies=auth)
    async def engineering_artifact(artifact_id: str):
        if engineer is None or "workspace.read" not in engine.actor.capabilities:
            raise HTTPException(403, "Engineer artifact access denied")
        try:
            return engineer.artifact(artifact_id, engine.actor.id)
        except (ValueError, FileNotFoundError):
            raise HTTPException(404, "Artifact not found") from None

    @app.get("/api/engineer/artifacts", dependencies=auth)
    async def engineering_run_artifacts(run_id: str):
        if engineer is None or "workspace.read" not in engine.actor.capabilities:
            raise HTTPException(403, "Engineer artifact access denied")
        try:
            return engineer.artifacts_for_run(run_id, engine.actor.id)
        except ValueError:
            raise HTTPException(422, "A run UUID is required") from None

    @app.get("/api/runs", dependencies=auth)
    async def runs(limit: Annotated[int, Query(ge=1, le=100)] = 30):
        async with db.sessions() as session:
            rows = (
                await session.execute(
                    select(AgentRun)
                    .where(AgentRun.actor_id == engine.actor.id)
                    .order_by(AgentRun.created_at.desc())
                    .limit(limit)
                )
            ).scalars()
            return [run_json(run) for run in rows]

    @app.get("/api/runs/{run_id}", dependencies=auth)
    async def get_run(run_id: str):
        async with db.sessions() as session:
            run = await engine._run(session, run_id, locked=False)
            result = run_json(run)
            rows = (
                await session.execute(
                    select(AgentStep)
                    .where(AgentStep.run_id == run_id)
                    .order_by(AgentStep.created_at)
                )
            ).scalars()
            result["steps"] = [
                {
                    "state": step.state,
                    "summary": step.summary,
                    "created_at": step.created_at.isoformat(),
                }
                for step in rows
            ]
            return result

    @app.get("/api/runs/{run_id}/events", dependencies=auth)
    async def run_events(run_id: str):
        await get_run(run_id)

        async def events():
            previous = None
            for _ in range(300):
                value = await get_run(run_id)
                encoded = json.dumps(value)
                if encoded != previous:
                    yield f"event: run\ndata: {encoded}\n\n"
                    previous = encoded
                if value["state"] in TERMINAL or value["state"] == "WAITING_FOR_APPROVAL":
                    return
                await asyncio.sleep(0.2)
            yield "event: reconnect\ndata: {}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.post("/api/runs/{run_id}/cancel", dependencies=auth)
    async def cancel(run_id: str):
        await engine.cancel(run_id)
        return await get_run(run_id)

    @app.get("/api/approvals", dependencies=auth)
    async def approvals():
        async with db.sessions() as session:
            rows = (
                await session.execute(
                    select(ApprovalRequest)
                    .where(ApprovalRequest.actor_id == engine.actor.id)
                    .order_by(ApprovalRequest.created_at.desc())
                    .limit(100)
                )
            ).scalars()
            return [
                {
                    "id": a.id,
                    "run_id": a.run_id,
                    "status": a.status,
                    "operation": a.operation,
                    "operation_hash": a.operation_hash,
                    "expires_at": a.expires_at.isoformat(),
                }
                for a in rows
            ]

    @app.post("/api/approvals/{approval_id}/approve", dependencies=auth)
    async def approve(approval_id: str):
        return {"run_id": await engine.approve(approval_id)}

    @app.post("/api/approvals/{approval_id}/reject", dependencies=auth)
    async def reject(approval_id: str):
        return {"run_id": await engine.reject(approval_id)}

    @app.get("/api/audit", dependencies=auth)
    async def audits():
        async with db.sessions() as session:
            rows = (
                await session.execute(
                    select(AuditEvent)
                    .where(AuditEvent.actor_id == engine.actor.id)
                    .order_by(AuditEvent.created_at.desc())
                    .limit(100)
                )
            ).scalars()
            return [
                {
                    "event": a.event,
                    "run_id": a.run_id,
                    "details": a.details,
                    "created_at": a.created_at.isoformat(),
                }
                for a in rows
            ]

    @app.get("/api/settings", dependencies=auth)
    async def settings_view():
        return {
            "provider": cfg.provider,
            "primary_model": cfg.primary_reasoning_model,
            "fallback_model": cfg.fallback_reasoning_model,
            "utility_model": cfg.utility_model,
            "fallback_enabled": cfg.allow_fallback,
            "voice": "not_implemented",
            "modes": [mode.value for mode in Mode],
            "checkpoint": "phase 7 Tutor; Game Master and product UI pending",
            "memory": {
                "embedding_provider": cfg.embedding_provider,
                "pgvector": cfg.memory_pgvector,
                "token_budget": cfg.memory_context_tokens,
            },
        }

    @app.get("/api/projects", dependencies=auth)
    async def projects():
        return [
            {"id": project_id, "kind": "REGISTERED_CODE_PROJECT"}
            for project_id in cfg.project_roots
        ]

    @app.get("/api/tools", dependencies=auth)
    async def tools_view():
        return registry.schemas()

    @app.post("/api/tools/execute", status_code=202, dependencies=auth)
    async def tools_execute(proposal: ToolProposal, mode: Mode = Mode.ENGINEER):
        await admit()
        try:
            registry.validate(proposal)
        except ValueError:
            raise HTTPException(422, "Unknown tool or invalid arguments") from None
        scope_fields = {}
        # This is an authenticated direct request; a model cannot set run context.
        if proposal.name.startswith(("engineer.", "sandbox.")):
            scope_fields["project_id"] = proposal.arguments["project_id"]
        if proposal.name.startswith("memory."):
            namespace = proposal.arguments.get("namespace", "personal")
            if ":" in namespace:
                kind, value = namespace.split(":", 1)
                scope_fields[f"{kind}_id"] = value
        if proposal.name.startswith("tutor."):
            scope_fields["learning_objective_id"] = proposal.arguments["objective_id"]
        return {
            "run_id": await engine.create(
                ChatRequest(message=f"Execute {proposal.name}", mode=mode, **scope_fields),
                direct=proposal,
            )
        }

    async def code_tool(project_id: str, name: str, arguments: dict):
        if project_id not in cfg.project_roots:
            raise HTTPException(404, "Project not registered")
        return await tools_execute(
            ToolProposal(
                name=name, arguments={"project_id": project_id, **arguments}, call_id="api-call"
            ),
            Mode.ENGINEER,
        )

    @app.get("/api/code/projects/{project_id}/graph", dependencies=auth, status_code=202)
    async def graph_health(project_id: str):
        return await code_tool(project_id, "graph.health", {})

    @app.post("/api/code/projects/{project_id}/graph/query", dependencies=auth, status_code=202)
    async def graph_query(project_id: str, body: QueryBody):
        return await code_tool(project_id, "graph.query", body.model_dump())

    @app.post("/api/code/projects/{project_id}/graph/path", dependencies=auth, status_code=202)
    async def graph_path(project_id: str, body: PathBody):
        return await code_tool(project_id, "graph.path", body.model_dump())

    @app.post("/api/code/projects/{project_id}/graph/update", dependencies=auth, status_code=202)
    async def graph_update(project_id: str):
        return await code_tool(project_id, "graph.update", {})

    return app
