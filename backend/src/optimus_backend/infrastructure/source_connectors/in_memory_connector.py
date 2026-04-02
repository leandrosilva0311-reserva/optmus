from fnmatch import fnmatch

from optimus_backend.core.source_connectors.protocols import SourceConnector


class InMemorySourceConnector(SourceConnector):
    def __init__(self, files: dict[str, str] | None = None) -> None:
        self._files = files or {}

    def fetch_file(self, path: str) -> str:
        if path not in self._files:
            raise KeyError(f"file '{path}' not found")
        return self._files[path]

    def list_files(self, pattern: str = "*") -> list[str]:
        return sorted([path for path in self._files if fnmatch(path, pattern)])

    def search(self, query: str) -> list[dict[str, object]]:
        normalized = query.lower()
        results: list[dict[str, object]] = []
        for path, content in self._files.items():
            for line_number, line in enumerate(content.splitlines(), start=1):
                if normalized not in line.lower():
                    continue
                results.append(
                    {
                        "path": path,
                        "line_number": line_number,
                        "line_range": [line_number, line_number],
                        "snippet": line[:200],
                    }
                )
        return sorted(results, key=lambda item: (str(item["path"]), int(item["line_number"])))
