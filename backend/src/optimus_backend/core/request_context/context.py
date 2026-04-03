from contextvars import ContextVar, Token

from optimus_backend.core.request_context.models import RequestContext

_REQUEST_CONTEXT: ContextVar[RequestContext | None] = ContextVar("request_context", default=None)


def set_request_context(context: RequestContext) -> Token[RequestContext | None]:
    return _REQUEST_CONTEXT.set(context)


def get_request_context() -> RequestContext | None:
    return _REQUEST_CONTEXT.get()


def reset_request_context(token: Token[RequestContext | None]) -> None:
    _REQUEST_CONTEXT.reset(token)
