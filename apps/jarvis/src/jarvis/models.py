import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol, cast

from jarvis.config import Settings
from jarvis.domain import Message, ModelResult, ToolProposal


class ProviderFailure(Exception):
    def __init__(self, code: str, *, retryable: bool = False):
        super().__init__(code)
        self.code = code
        self.retryable = retryable
        self.attempts: list[dict[str, str]] = []


class ModelProvider(Protocol):
    async def respond(
        self, model: str, messages: list[Message], tools: list[dict[str, Any]]
    ) -> ModelResult: ...


class FakeModelProvider:
    """Offline protocol exercise; never pretends to provide live intelligence."""

    async def respond(self, model, messages, tools) -> ModelResult:
        if messages[-1].role == "tool":
            return ModelResult(text="[FAKE] Tool completed. Evidence: " + messages[-1].text[:1800])
        request = next(m.text for m in reversed(messages) if m.role == "user")
        match = re.fullmatch(r"\[tool:([\w.]+)\]\s*(\{.*\})", request, re.DOTALL)
        if match:
            return ModelResult(
                tools=[
                    ToolProposal(
                        name=match[1], arguments=json.loads(match[2]), call_id="fake-call-1"
                    )
                ]
            )
        return ModelResult(text="[FAKE] Request recorded. Configure OpenAI for live reasoning.")


class OpenAIModelProvider:
    def __init__(self, settings: Settings, client=None):
        self.settings = settings
        self.client = client

    async def respond(self, model, messages, tools) -> ModelResult:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            AsyncOpenAI,
            AsyncStream,
            AuthenticationError,
        )
        from openai.types.responses import (
            Response,
            ResponseInputParam,
            ResponseStreamEvent,
            ToolParam,
        )

        if self.client is None:
            try:
                self.client = AsyncOpenAI(timeout=self.settings.model_timeout, max_retries=0)
            except Exception as exc:
                raise ProviderFailure("authentication_configuration_missing") from exc

        names = {tool["name"].replace(".", "__"): tool["name"] for tool in tools}
        inputs: list[dict[str, Any]] = []
        for message in messages:
            if message.role == "assistant_tool":
                inputs.append(
                    {
                        "type": "function_call",
                        "call_id": message.call_id,
                        "name": message.name.replace(".", "__"),
                        "arguments": json.dumps(message.arguments),
                    }
                )
            elif message.role == "tool":
                inputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": message.call_id,
                        "output": message.text,
                    }
                )
            else:
                inputs.append({"role": message.role, "content": message.text})
        definitions = [
            {
                "type": "function",
                "name": name,
                "description": tool["description"],
                "parameters": tool["parameters"],
            }
            for name, tool in zip(names, tools, strict=True)
        ]
        try:
            response = await self.client.responses.create(
                model=model,
                input=cast(ResponseInputParam, inputs),
                tools=cast(list[ToolParam], definitions),
                parallel_tool_calls=False,
                reasoning={"effort": self.settings.reasoning_effort},
                max_output_tokens=self.settings.max_output_tokens,
                store=False,
                stream=self.settings.stream_responses,
            )
            if self.settings.stream_responses:
                stream = cast(AsyncStream[ResponseStreamEvent], response)
                final = None
                try:
                    async for event in stream:
                        if event.type == "response.completed":
                            final = event.response
                        elif event.type in {"response.failed", "error"}:
                            raise ProviderFailure("stream_failed")
                finally:
                    await stream.close()
                if final is None:
                    raise ProviderFailure("stream_incomplete")
                response = final
            else:
                response = cast(Response, response)
        except AuthenticationError as exc:
            raise ProviderFailure("authentication_failed") from exc
        except APITimeoutError as exc:
            raise ProviderFailure("provider_timeout", retryable=True) from exc
        except APIConnectionError as exc:
            raise ProviderFailure("connection_failed", retryable=True) from exc
        except APIStatusError as exc:
            code = "model_unavailable" if exc.status_code == 404 else "provider_error"
            if exc.status_code == 429:
                code = "rate_limited"
            raise ProviderFailure(code, retryable=exc.status_code in {404, 429, 502, 503}) from exc
        calls = []
        if getattr(response, "status", "completed") != "completed":
            raise ProviderFailure("response_incomplete")
        for item in response.output:
            if item.type == "function_call":
                try:
                    args = json.loads(item.arguments)
                    calls.append(
                        ToolProposal(
                            name=names.get(item.name, item.name),
                            arguments=args,
                            call_id=item.call_id,
                        )
                    )
                except (ValueError, TypeError) as exc:
                    raise ProviderFailure("invalid_tool_response") from exc
        usage = response.usage
        return ModelResult(
            text=response.output_text,
            tools=calls,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close()


@dataclass(frozen=True)
class RoutedResult:
    response: ModelResult
    model: str
    fallback_from: str | None
    attempts: list[dict[str, str]]


class ModelRouter:
    def __init__(self, settings: Settings, provider: ModelProvider):
        self.settings = settings
        self.provider = provider

    def select_model(self, utility: bool = False, high_stakes: bool = False) -> str:
        cfg = self.settings
        if utility and cfg.utility_model and not high_stakes:
            return cfg.utility_model
        return cfg.primary_reasoning_model

    async def respond(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]],
        *,
        utility: bool = False,
        allow_fallback: bool = False,
        high_stakes: bool = False,
    ) -> RoutedResult:
        cfg = self.settings
        primary = self.select_model(utility, high_stakes)
        attempts: list[dict[str, str]] = []
        try:
            result = await asyncio.wait_for(
                self.provider.respond(primary, messages, tools), cfg.model_timeout
            )
            return RoutedResult(result, primary, None, [{"model": primary, "status": "ok"}])
        except TimeoutError:
            failure = ProviderFailure("provider_timeout", retryable=True)
        except ProviderFailure as exc:
            failure = exc
        attempts.append({"model": primary, "status": failure.code})
        failure.attempts = attempts
        if not (
            cfg.allow_fallback
            and allow_fallback
            and not high_stakes
            and failure.retryable
            and cfg.fallback_reasoning_model
            and cfg.fallback_reasoning_model != primary
        ):
            raise failure
        try:
            result = await asyncio.wait_for(
                self.provider.respond(cfg.fallback_reasoning_model, messages, tools),
                cfg.model_timeout,
            )
        except (TimeoutError, ProviderFailure) as exc:
            fallback_failure = (
                exc
                if isinstance(exc, ProviderFailure)
                else ProviderFailure("provider_timeout", retryable=True)
            )
            fallback_failure.attempts = [
                *attempts,
                {"model": cfg.fallback_reasoning_model, "status": fallback_failure.code},
            ]
            raise fallback_failure from exc
        attempts.append({"model": cfg.fallback_reasoning_model, "status": "ok"})
        return RoutedResult(result, cfg.fallback_reasoning_model, primary, attempts)
