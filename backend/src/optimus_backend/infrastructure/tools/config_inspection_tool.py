import json


class ConfigInspectionTool:
    name = "config_inspection"

    def run(self, payload: dict) -> tuple[str, bool]:
        config_text = str(payload.get("config_text", "")).strip()
        if not config_text:
            raise ValueError("config_text is required")

        try:
            parsed = json.loads(config_text)
            top_level = sorted(parsed.keys()) if isinstance(parsed, dict) else []
            return f"json_valid=true top_level_keys={','.join(top_level[:30])}", False
        except Exception:
            lines = config_text.splitlines()
            suspicious = [line.strip() for line in lines if "TODO" in line or "password" in line.lower()]
            return f"json_valid=false lines={len(lines)} suspicious_items={len(suspicious)}", False
