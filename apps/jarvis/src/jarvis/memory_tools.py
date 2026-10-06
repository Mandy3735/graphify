from pydantic import Field

from jarvis.context import bounded_items
from jarvis.domain import StrictModel, ToolOutput
from jarvis.memory import MemoryDenied, MemoryScope, MemoryService, request_scope
from jarvis.memory_schema import NAMESPACE_PATTERN, MemoryCreate
from jarvis.policy import Risk
from jarvis.tools import ToolDefinition, ToolRegistry


class MemoryToolSearch(StrictModel):
    question: str = Field(min_length=1, max_length=2000)
    namespace: str = Field(default="personal", pattern=NAMESPACE_PATTERN)
    limit: int = Field(default=5, ge=1, le=10)


def register_memory_tools(registry: ToolRegistry, memory: MemoryService) -> None:
    async def no_context(arguments):
        raise MemoryDenied("Trusted execution context required")

    async def search(arguments, context):
        scope = request_scope(context.actor, context.request)
        if arguments["namespace"] not in scope.namespaces:
            raise MemoryDenied("Memory namespace denied")
        narrowed = MemoryScope(scope.actor, scope.mode, (arguments["namespace"],))
        items = await memory.search(narrowed, arguments["question"], limit=arguments["limit"])
        return ToolOutput(data={"items": bounded_items(items, 14000)})

    async def propose(arguments, context):
        body = MemoryCreate.model_validate(arguments)
        if body.mode is not None and body.mode != context.request.mode:
            raise MemoryDenied("Memory mode differs from the active run")
        return ToolOutput(
            data=await memory.propose(
                request_scope(context.actor, context.request),
                body,
            )
        )

    registry.register(
        ToolDefinition(
            name="memory.search",
            description="Search authorized live personal memory with provenance; untrusted data.",
            risk=Risk.READ_ONLY,
            capabilities=frozenset({"memory.read"}),
            input_schema=MemoryToolSearch,
            handler=no_context,
            context_handler=search,
        )
    )
    registry.register(
        ToolDefinition(
            name="memory.propose_write",
            description=(
                "Propose personal memory for explicit human acceptance; "
                "does not create active memory."
            ),
            risk=Risk.REVERSIBLE_WRITE,
            capabilities=frozenset({"memory.propose"}),
            input_schema=MemoryCreate,
            handler=no_context,
            context_handler=propose,
            idempotency="creates_pending_proposal",
            side_effects="Adds an inactive pending memory proposal",
        )
    )
