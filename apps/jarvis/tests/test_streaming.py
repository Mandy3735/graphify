from types import SimpleNamespace

import pytest

from jarvis.domain import Message
from jarvis.models import OpenAIModelProvider, ProviderFailure


class Stream:
    def __init__(self, event):
        self.event, self.closed = event, False

    def __aiter__(self):
        return self.events()

    async def events(self):
        yield SimpleNamespace(type="response.output_text.delta", delta="ignored partial text")
        yield self.event

    async def close(self):
        self.closed = True


@pytest.mark.parametrize("kind", ["response.completed", "response.failed", "response.incomplete"])
async def test_responses_stream_closes_and_only_completed_output_is_authoritative(settings, kind):
    stream = Stream(
        SimpleNamespace(
            type=kind,
            response=SimpleNamespace(
                output_text="completed answer", output=[], usage=None, status="completed"
            ),
        )
    )

    class Responses:
        async def create(self, **kwargs):
            assert kwargs["stream"] is True
            return stream

    provider = OpenAIModelProvider(settings, SimpleNamespace(responses=Responses()))
    if kind == "response.completed":
        result = await provider.respond("configured", [Message(role="user", text="test")], [])
        assert result.text == "completed answer"
    else:
        with pytest.raises(ProviderFailure):
            await provider.respond("configured", [], [])
    assert stream.closed
