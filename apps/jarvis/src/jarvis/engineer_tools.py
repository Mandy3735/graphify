from jarvis.domain import Mode, ToolOutput
from jarvis.engineer import EngineerService
from jarvis.engineer_schema import ChangeRequest, SandboxRequest
from jarvis.policy import Risk
from jarvis.tools import ToolDefinition, ToolRegistry


def register_engineer_tools(registry: ToolRegistry, service: EngineerService) -> None:
    async def context_required(arguments):
        raise ValueError("Actual run context required")

    async def change(arguments, context):
        return ToolOutput(
            data=await service.change(ChangeRequest.model_validate(arguments), context)
        )

    async def run(arguments, context):
        return ToolOutput(
            data=await service.run_command(SandboxRequest.model_validate(arguments), context)
        )

    registry.register(
        ToolDefinition(
            name="engineer.change",
            description="Graph-first isolated change, tests, diff and impact. "
            "Requires exact source hashes. Dry run produces a proposal without execution.",
            risk=Risk.REVERSIBLE_WRITE,
            capabilities=frozenset(
                {
                    "engineer.write",
                    "engineer.execute",
                    "graph.read",
                    "graph.write",
                    "workspace.read",
                }
            ),
            input_schema=ChangeRequest,
            handler=context_required,
            context_handler=change,
            timeout=service.cfg.run_timeout,
            idempotency="never_replay",
            side_effects="Private worktree, optional source graph indexing, retained artifact; "
            "no source application, merge, push or deploy",
            modes=frozenset({Mode.ENGINEER.value}),
        )
    )
    for name in ["sandbox.run_command", "sandbox.run_tests"]:
        registry.register(
            ToolDefinition(
                name=name,
                description="Bounded system Python command in verified offline OS sandbox.",
                risk=Risk.REVERSIBLE_WRITE,
                capabilities=frozenset({"engineer.execute", "workspace.read"}),
                input_schema=SandboxRequest,
                handler=context_required,
                context_handler=run,
                timeout=service.cfg.sandbox_timeout + 10,
                idempotency="never_replay",
                side_effects="Ephemeral read-only snapshot and private tmpfs; retained report",
                modes=frozenset({Mode.ENGINEER.value}),
            )
        )
