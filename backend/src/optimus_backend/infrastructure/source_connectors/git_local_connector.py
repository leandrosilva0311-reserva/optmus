from __future__ import annotations

from pathlib import Path

from optimus_backend.core.source_connectors.protocols import SourceConnector
from optimus_backend.settings.config import config


class GitLocalSourceConnector(SourceConnector):
    """
    Local repository connector validated by `.git` presence.

    This connector performs filesystem reads only and does not execute Git commands.
    """

    def __init__(self, repo_root: str) -> None:
        root = Path(repo_root).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("repo_root must be an existing directory")
        if not (root / ".git").exists():
            raise ValueError("repo_root must contain a .git directory")
        self._root = root
        self._allowed_extensions = {ext.lower() for ext in config.local_connector_allowed_extensions}
        self._ignored_dirs = {name for name in config.local_connector_ignored_dirs}
        self._max_file_bytes = config.local_connector_max_file_bytes
        self._search_max_results = config.local_connector_search_max_results

    def _resolve_path(self, path: str) -> Path:
        candidate = (self._root / path).resolve()
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise ValueError("path traversal outside repository is not allowed") from exc
        return candidate

    def fetch_file(self, path: str) -> str:
        file_path = self._resolve_path(path)
        if not file_path.exists() or not file_path.is_file():
            raise KeyError(f"file '{path}' not found")
        size = file_path.stat().st_size
        if size > self._max_file_bytes:
            raise ValueError(f"file '{path}' exceeds max allowed size of {self._max_file_bytes} bytes")
        try:
            return file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"file '{path}' is not a UTF-8 text file") from exc

    def _is_included(self, path: Path) -> bool:
        if any(part in self._ignored_dirs for part in path.parts):
            return False
        suffix = path.suffix.lower()
        return not self._allowed_extensions or suffix in self._allowed_extensions

    def list_files(self, pattern: str = "*") -> list[str]:
        if pattern.count("[") != pattern.count("]"):
            raise ValueError(f"invalid file pattern '{pattern}'")
        try:
            return sorted(
                str(path.relative_to(self._root))
                for path in self._root.rglob(pattern)
                if path.is_file() and self._is_included(path)
            )
        except Exception as exc:
            raise ValueError(f"invalid file pattern '{pattern}'") from exc

    def search(self, query: str) -> list[dict[str, object]]:
        normalized = query.lower()
        matches: list[dict[str, object]] = []
        for file_path in self.list_files("**/*"):
            abs_path = self._resolve_path(file_path)
            try:
                content = abs_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                if normalized not in line.lower():
                    continue
                matches.append(
                    {
                        "path": file_path,
                        "line_number": line_number,
                        "line_range": [line_number, line_number],
                        "snippet": line[:200],
                    }
                )
                if len(matches) >= self._search_max_results:
                    return matches
        return sorted(matches, key=lambda item: (str(item["path"]), int(item["line_number"])))
