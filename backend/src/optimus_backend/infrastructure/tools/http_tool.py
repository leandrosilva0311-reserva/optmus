import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class HttpTool:
    name = "http"

    def __init__(
        self,
        allowed_domains: set[str] | None = None,
        allowed_methods: set[str] | None = None,
        timeout_seconds: int = 4,
        retry_count: int = 2,
    ) -> None:
        self._allowed_domains = allowed_domains or {"api.github.com", "example.com"}
        self._allowed_methods = allowed_methods or {"GET"}
        self._timeout_seconds = timeout_seconds
        self._retry_count = retry_count

    def run(self, payload: dict) -> tuple[str, bool]:
        method = payload.get("method", "GET").upper()
        url = payload.get("url", "")
        if method not in self._allowed_methods:
            raise PermissionError("http method not allowed")

        host = urlparse(url).hostname or ""
        if host not in self._allowed_domains:
            raise PermissionError("domain not allowed")

        last_error: Exception | None = None
        for _ in range(self._retry_count + 1):
            try:
                req = Request(url=url, method=method)
                with urlopen(req, timeout=self._timeout_seconds) as response:
                    data = response.read(4000).decode("utf-8", errors="replace")
                    return data, False
            except Exception as exc:  # pragma: no cover
                last_error = exc
                time.sleep(0.1)

        raise RuntimeError(f"http request failed: {last_error}")
