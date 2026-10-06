from types import SimpleNamespace

import httpx
import pytest

from jarvis.models import OpenAIModelProvider, ProviderFailure


@pytest.mark.parametrize(
    "kind,code,retryable",
    [
        ("auth", "authentication_failed", False),
        ("not_found", "model_unavailable", True),
        ("rate", "rate_limited", True),
        ("timeout", "provider_timeout", True),
        ("connection", "connection_failed", True),
        ("forbidden", "provider_error", False),
        ("server", "provider_error", True),
    ],
)
async def test_official_sdk_errors_are_safe_domain_errors(settings, kind, code, retryable):
    from openai import (
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        InternalServerError,
        NotFoundError,
        PermissionDeniedError,
        RateLimitError,
    )

    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    if kind == "timeout":
        failure = APITimeoutError(request)
    elif kind == "connection":
        failure = APIConnectionError(request=request, message="private provider detail")
    else:
        status, exception = {
            "auth": (401, AuthenticationError),
            "not_found": (404, NotFoundError),
            "rate": (429, RateLimitError),
            "forbidden": (403, PermissionDeniedError),
            "server": (503, InternalServerError),
        }[kind]
        failure = exception(
            "private provider detail", response=httpx.Response(status, request=request), body=None
        )

    class Responses:
        async def create(self, **kwargs):
            raise failure

    provider = OpenAIModelProvider(settings, SimpleNamespace(responses=Responses()))
    with pytest.raises(ProviderFailure) as captured:
        await provider.respond("configured", [], [])
    assert captured.value.code == code and captured.value.retryable is retryable
    assert "private provider detail" not in str(captured.value)
