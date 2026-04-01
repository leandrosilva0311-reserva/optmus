import shlex
import subprocess


class TerminalTool:
    name = "terminal"

    def __init__(self, allowed_commands: set[str] | None = None, timeout_seconds: int = 5, max_output: int = 3000) -> None:
        self._allowed_commands = allowed_commands or {"echo", "pwd", "ls", "python", "pytest"}
        self._timeout_seconds = timeout_seconds
        self._max_output = max_output

    def run(self, payload: dict) -> tuple[str, bool]:
        command_text = payload.get("command", "")
        parts = shlex.split(command_text)
        if not parts:
            raise ValueError("command is required")
        if parts[0] not in self._allowed_commands:
            raise PermissionError(f"command '{parts[0]}' not allowed")

        result = subprocess.run(parts, capture_output=True, text=True, timeout=self._timeout_seconds, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        truncated = len(output) > self._max_output
        if truncated:
            output = output[: self._max_output]
        return output, truncated
