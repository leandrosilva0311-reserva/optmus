import json
from dataclasses import dataclass

from optimus_backend.core.source_connectors.protocols import SourceConnector
from optimus_backend.settings.config import config

SUPPORTED_SCENARIOS = {"bug_diagnosis", "refactor_suggestion"}


@dataclass(slots=True)
class RepoEnrichmentOutcome:
    inputs: dict[str, object]
    attempted: bool
    applied: bool
    scenario_id: str
    listed_files: int
    selected_files: int
    search_hits: int
    skipped_reason: str | None = None



def _repo_enrichment_enabled(inputs: dict[str, object]) -> bool:
    raw = inputs.get("repo_enrichment")
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, dict):
        return bool(raw.get("enabled"))
    return False



def _candidate_paths(
    scenario_id: str,
    connector: SourceConnector,
    file_pattern: str,
    query_text: str,
) -> tuple[list[str], int]:
    listed_paths = connector.list_files(file_pattern)
    listed_set = set(listed_paths)
    search_hits = connector.search(query_text) if query_text else []
    ranked_from_search = [str(hit.get("path", "")) for hit in search_hits if str(hit.get("path", "")).strip()]

    ordered_candidates: list[str] = []
    for path in ranked_from_search + listed_paths:
        if path in listed_set and path not in ordered_candidates:
            ordered_candidates.append(path)

    if scenario_id == "bug_diagnosis":
        # bug diagnosis prioritiza forte sinal de search
        limited_candidates = ordered_candidates[: max(10, config.repo_enrichment_max_files)]
    else:
        limited_candidates = ordered_candidates

    return limited_candidates, len(search_hits)



def enrich_repo_inputs_for_scenario(
    scenario_id: str,
    inputs: dict[str, object],
    source_connector_factory: type[SourceConnector] | None,
) -> RepoEnrichmentOutcome:
    if scenario_id not in SUPPORTED_SCENARIOS:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, "scenario_not_supported")

    if source_connector_factory is None:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, "connector_unavailable")

    if "files" in inputs:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, "files_already_provided")

    if not _repo_enrichment_enabled(inputs):
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, "repo_enrichment_disabled")

    repo_path = str(inputs.get("repo_path", "")).strip()
    if not repo_path:
        return RepoEnrichmentOutcome(inputs, True, False, scenario_id, 0, 0, 0, "repo_path_missing")

    file_pattern = str(inputs.get("file_pattern", "**/*")).strip() or "**/*"
    query_text = str(inputs.get("observed_error") if scenario_id == "bug_diagnosis" else inputs.get("objective", "")).strip()

    connector = source_connector_factory(repo_path)
    candidate_paths, search_hits = _candidate_paths(scenario_id, connector, file_pattern, query_text)
    if len(candidate_paths) > config.repo_enrichment_max_files:
        raise ValueError(
            f"repo enrichment exceeded max files: {len(candidate_paths)} > {config.repo_enrichment_max_files}. "
            "Narrow file_pattern or provide files explicitly."
        )

    total_bytes = 0
    selected_files: list[dict[str, str]] = []
    for path in candidate_paths:
        content = connector.fetch_file(path)
        content_bytes = len(content.encode("utf-8"))
        total_bytes += content_bytes
        if total_bytes > config.repo_enrichment_max_total_bytes:
            raise ValueError(
                f"repo enrichment exceeded total limit: {total_bytes} > {config.repo_enrichment_max_total_bytes} bytes. "
                "Narrow file_pattern or provide files explicitly."
            )
        selected_files.append({"path": path, "content": content})

    enriched = dict(inputs)
    enriched["files"] = selected_files
    return RepoEnrichmentOutcome(
        inputs=enriched,
        attempted=True,
        applied=True,
        scenario_id=scenario_id,
        listed_files=len(candidate_paths),
        selected_files=len(selected_files),
        search_hits=search_hits,
        skipped_reason=None,
    )



def to_audit_payload(outcome: RepoEnrichmentOutcome) -> str:
    payload = {
        "scenario_id": outcome.scenario_id,
        "attempted": outcome.attempted,
        "applied": outcome.applied,
        "listed_files": outcome.listed_files,
        "selected_files": outcome.selected_files,
        "search_hits": outcome.search_hits,
        "skipped_reason": outcome.skipped_reason,
    }
    return json.dumps(payload, sort_keys=True)
