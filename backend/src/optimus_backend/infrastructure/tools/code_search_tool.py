import re


class CodeSearchTool:
    name = "code_search"

    def run(self, payload: dict) -> tuple[str, bool]:
        query = str(payload.get("query", "")).strip()
        files = payload.get("files", [])
        if not query:
            raise ValueError("query is required")
        if not isinstance(files, list):
            raise ValueError("files must be a list")

        results: list[str] = []
        pattern = re.compile(re.escape(query), flags=re.IGNORECASE)
        for item in files:
            path = str(item.get("path", "")) if isinstance(item, dict) else ""
            content = str(item.get("content", "")) if isinstance(item, dict) else ""
            if not path or not content:
                continue
            for idx, line in enumerate(content.splitlines(), start=1):
                if pattern.search(line):
                    results.append(f"{path}:{idx}:{line[:180]}")
                    if len(results) >= 120:
                        return "\n".join(results), True
        return "\n".join(results) if results else "no_matches", False
