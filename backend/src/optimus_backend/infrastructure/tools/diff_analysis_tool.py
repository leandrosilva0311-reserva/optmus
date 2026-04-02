class DiffAnalysisTool:
    name = "diff_analysis"

    def run(self, payload: dict) -> tuple[str, bool]:
        diff_text = str(payload.get("diff_text", "")).strip()
        if not diff_text:
            raise ValueError("diff_text is required")

        added = 0
        removed = 0
        touched_files = 0
        for line in diff_text.splitlines():
            if line.startswith("+++ "):
                touched_files += 1
            elif line.startswith("+") and not line.startswith("+++"):
                added += 1
            elif line.startswith("-") and not line.startswith("---"):
                removed += 1

        summary = (
            f"touched_files={touched_files} added_lines={added} removed_lines={removed} "
            f"change_size={'large' if (added + removed) > 200 else 'medium' if (added + removed) > 50 else 'small'}"
        )
        return summary, False
