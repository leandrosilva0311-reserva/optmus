from pathlib import Path


class FilesystemTool:
    name = "filesystem"

    def __init__(self, project_root: str) -> None:
        self._root = Path(project_root).resolve()

    def run(self, payload: dict) -> tuple[str, bool]:
        action = payload.get("action", "read")
        relative_path = payload.get("path", "")
        target = (self._root / relative_path).resolve()

        if self._root not in target.parents and target != self._root:
            raise PermissionError("path traversal blocked")

        if action == "read":
            text = target.read_text()[:4000]
            truncated = len(target.read_text()) > 4000
            return text, truncated

        if action == "list":
            items = [p.name for p in target.iterdir()][:200]
            return "\n".join(items), False

        raise ValueError("unsupported filesystem action")
