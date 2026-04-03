class LogAnalysisTool:
    name = "log_analysis"

    def run(self, payload: dict) -> tuple[str, bool]:
        log_text = str(payload.get("log_text", "")).strip()
        if not log_text:
            raise ValueError("log_text is required")

        lines = log_text.splitlines()
        errors = [line for line in lines if "error" in line.lower() or "exception" in line.lower()]
        warnings = [line for line in lines if "warn" in line.lower()]
        return (
            f"lines={len(lines)} errors={len(errors)} warnings={len(warnings)} "
            f"sample_error={(errors[0][:180] if errors else 'none')}",
            False,
        )
