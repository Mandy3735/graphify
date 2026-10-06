from typing import Annotated

from fastapi import APIRouter, Query, Response

from jarvis.domain import Mode
from jarvis.memory import MemoryScope, MemoryService
from jarvis.memory_schema import (
    NAMESPACE_PATTERN,
    MemoryCorrection,
    MemoryCreate,
    MemorySearch,
)
from jarvis.policy import Actor

NamespaceQuery = Annotated[str, Query(pattern=NAMESPACE_PATTERN)]


def memory_router(memory: MemoryService, actor: Actor, dependencies: list) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["personal memory"], dependencies=dependencies)

    @router.get("/memories")
    async def list_memories(
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        after: Annotated[str, Query(max_length=36)] = "",
        include_history: bool = False,
    ):
        return await memory.list_items(
            MemoryScope(actor, mode, (namespace,)),
            limit=limit,
            after=after,
            include_history=include_history,
        )

    @router.get("/memories/export")
    async def export_memories(
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
        limit: Annotated[int, Query(ge=1, le=100)] = 100,
        after: Annotated[str, Query(max_length=36)] = "",
        include_history: bool = False,
    ):
        result = await memory.list_items(
            MemoryScope(actor, mode, (namespace,)),
            limit=limit,
            after=after,
            include_history=include_history,
        )
        return {"format": "jarvis-personal-memory-v1", **result}

    @router.post("/memories/search")
    async def search_memories(body: MemorySearch):
        return {
            "items": await memory.search(
                MemoryScope(actor, body.mode, (body.namespace,)),
                body.question,
                limit=body.limit,
            )
        }

    @router.post("/memories", status_code=201)
    async def create_memory(body: MemoryCreate, mode: Mode = Mode.CHIEF_OF_STAFF):
        return await memory.create(MemoryScope(actor, mode, (body.namespace,)), body)

    @router.get("/memories/{memory_id}")
    async def inspect_memory(
        memory_id: str,
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
    ):
        return await memory.inspect(MemoryScope(actor, mode, (namespace,)), memory_id)

    @router.patch("/memories/{memory_id}")
    async def correct_memory(
        memory_id: str,
        body: MemoryCorrection,
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
    ):
        return await memory.correct(MemoryScope(actor, mode, (namespace,)), memory_id, body)

    @router.delete("/memories/{memory_id}", status_code=204)
    async def delete_memory(
        memory_id: str,
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
    ):
        await memory.delete(MemoryScope(actor, mode, (namespace,)), memory_id)
        return Response(status_code=204)

    @router.get("/memory-proposals")
    async def proposals(namespace: NamespaceQuery = "personal", mode: Mode = Mode.CHIEF_OF_STAFF):
        return await memory.proposals(MemoryScope(actor, mode, (namespace,)))

    @router.post("/memory-proposals/{proposal_id}/accept")
    async def accept_proposal(
        proposal_id: str,
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
    ):
        return await memory.decide_proposal(
            MemoryScope(actor, mode, (namespace,)), proposal_id, accept=True
        )

    @router.post("/memory-proposals/{proposal_id}/reject")
    async def reject_proposal(
        proposal_id: str,
        namespace: NamespaceQuery = "personal",
        mode: Mode = Mode.CHIEF_OF_STAFF,
    ):
        return await memory.decide_proposal(
            MemoryScope(actor, mode, (namespace,)), proposal_id, accept=False
        )

    return router
