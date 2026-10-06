import asyncio
from dataclasses import replace

import pytest
from pydantic import ValidationError

from jarvis.domain import Message, ModelResult, StrictModel, ToolOutput, ToolProposal
from jarvis.models import ModelRouter, OpenAIModelProvider, ProviderFailure
from jarvis.policy import Actor, Decision, PolicyEngine, Risk, operation_for, operation_hash
from jarvis.tools import ToolDefinition, ToolRegistry


class Input(StrictModel):
    target: str
    value: int = 1


async def handler(arguments):
    return ToolOutput(data=arguments)


def definition(risk):
    return ToolDefinition(
        "test.write", "Test operation", risk, frozenset({"write"}), Input, handler
    )


@pytest.mark.parametrize(
    "risk,expected",
    [
        (Risk.READ_ONLY, Decision.ALLOW),
        (Risk.REVERSIBLE_WRITE, Decision.ALLOW),
        (Risk.EXTERNAL_WRITE, Decision.REQUIRE_APPROVAL),
        (Risk.DESTRUCTIVE, Decision.REQUIRE_APPROVAL),
        (Risk.SAFETY_CRITICAL, Decision.DENY),
    ],
)
def test_risk_and_capability_precede_approval(risk, expected):
    policy = PolicyEngine()
    tool = definition(risk)
    assert policy.evaluate(Actor("actor", frozenset({"write"})), tool, {}, "ENGINEER") == expected
    assert policy.evaluate(Actor("actor", frozenset()), tool, {}, "ENGINEER") == Decision.DENY
    assert (
        policy.evaluate(
            Actor("actor", frozenset({"write"})),
            replace(tool, modes=frozenset({"TUTOR"})),
            {},
            "ENGINEER",
        )
        == Decision.DENY
    )


def test_strict_tool_schema_normalization_and_hash_binding():
    registry = ToolRegistry()
    registry.register(definition(Risk.EXTERNAL_WRITE))
    tool, args = registry.validate(ToolProposal(name="test.write", arguments={"target": "sample"}))
    assert args == {"target": "sample", "value": 1}
    operation = operation_for(tool, args)
    original = operation_hash(operation, "user", "run", "nonce", "expires")
    assert original == operation_hash(operation, "user", "run", "nonce", "expires")
    for actor, run, nonce, expiry in [
        ("other", "run", "nonce", "expires"),
        ("user", "other", "nonce", "expires"),
        ("user", "run", "other", "expires"),
        ("user", "run", "nonce", "other"),
    ]:
        assert original != operation_hash(operation, actor, run, nonce, expiry)
    assert original != operation_hash(
        operation_for(tool, {"target": "sample", "value": 2}), "user", "run", "nonce", "expires"
    )
    with pytest.raises(ValidationError):
        registry.validate(
            ToolProposal(
                name="test.write", arguments={"target": "sample", "capabilities": ["root"]}
            )
        )
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.validate(ToolProposal(name="grant.root", arguments={}))


class ScriptedModel:
    def __init__(self, primary_failure=None, delay=0):
        self.failure, self.delay, self.calls = primary_failure, delay, []

    async def respond(self, model, messages, tools):
        self.calls.append(model)
        await asyncio.sleep(self.delay)
        if len(self.calls) == 1 and self.failure:
            raise self.failure
        return ModelResult(text="ok", input_tokens=3, output_tokens=2)


@pytest.mark.parametrize(
    "allow_request,allow_server,high_stakes,auth,expected_fallback",
    [
        (True, True, False, False, True),
        (False, True, False, False, False),
        (True, False, False, False, False),
        (True, True, True, False, False),
        (True, True, False, True, False),
    ],
)
async def test_fallback_is_explicit_and_never_hides_auth_failure(
    settings, allow_request, allow_server, high_stakes, auth, expected_fallback
):
    cfg = settings.model_copy(
        update={
            "allow_fallback": allow_server,
            "primary_reasoning_model": "primary-configured",
            "fallback_reasoning_model": "replacement-configured",
        }
    )
    model = ScriptedModel(
        ProviderFailure("auth" if auth else "model_unavailable", retryable=not auth)
    )
    router = ModelRouter(cfg, model)
    if expected_fallback:
        result = await router.respond([], [], allow_fallback=allow_request, high_stakes=high_stakes)
        assert result.model == "replacement-configured"
        assert result.fallback_from == "primary-configured"
        assert result.attempts[0]["status"] == "model_unavailable"
    else:
        with pytest.raises(ProviderFailure):
            await router.respond([], [], allow_fallback=allow_request, high_stakes=high_stakes)
        assert model.calls == ["primary-configured"]


async def test_configured_utility_and_timeout(settings):
    cfg = settings.model_copy(update={"utility_model": "configured-cheap", "model_timeout": 0.01})
    model = ScriptedModel()
    result = await ModelRouter(cfg, model).respond([], [], utility=True)
    assert result.model == "configured-cheap"
    with pytest.raises(ProviderFailure, match="provider_timeout"):
        await ModelRouter(cfg, ScriptedModel(delay=0.1)).respond([], [])


async def test_high_stakes_cannot_route_to_utility_and_failed_fallback_is_reported(settings):
    cfg = settings.model_copy(
        update={
            "utility_model": "cheap",
            "primary_reasoning_model": "primary",
            "fallback_reasoning_model": "fallback",
            "allow_fallback": True,
        }
    )
    assert ModelRouter(cfg, ScriptedModel()).select_model(True, True) == "primary"

    class Unavailable:
        async def respond(self, *args):
            raise ProviderFailure("model_unavailable", retryable=True)

    with pytest.raises(ProviderFailure) as captured:
        await ModelRouter(cfg, Unavailable()).respond([], [], allow_fallback=True)
    assert captured.value.attempts == [
        {"model": "primary", "status": "model_unavailable"},
        {"model": "fallback", "status": "model_unavailable"},
    ]


async def test_openai_responses_adapter_and_function_history(settings):
    from types import SimpleNamespace

    captured = []

    class Responses:
        async def create(self, **kwargs):
            captured.append(kwargs)
            return SimpleNamespace(
                output_text="",
                usage=SimpleNamespace(input_tokens=7, output_tokens=4),
                output=[
                    SimpleNamespace(
                        type="function_call",
                        name="graph__query",
                        arguments='{"project_id":"fixture","question":"calls"}',
                        call_id="wire-id",
                    )
                ],
            )

    provider = OpenAIModelProvider(
        settings.model_copy(update={"stream_responses": False}),
        client=SimpleNamespace(responses=Responses()),
    )
    messages = [
        Message(role="user", text="query"),
        Message(
            role="assistant_tool",
            text="",
            name="graph.query",
            call_id="previous",
            arguments={"project_id": "fixture", "question": "calls"},
        ),
        Message(role="tool", text="untrusted result", call_id="previous"),
    ]
    response = await provider.respond(
        "model-configured",
        messages,
        [{"name": "graph.query", "description": "Query", "parameters": {"type": "object"}}],
    )
    assert response.tools[0].name == "graph.query"
    assert response.input_tokens == 7
    assert captured[0]["model"] == "model-configured"
    assert captured[0]["store"] is False
    assert captured[0]["parallel_tool_calls"] is False
    assert captured[0]["input"][1]["type"] == "function_call"
    assert captured[0]["input"][2]["type"] == "function_call_output"
