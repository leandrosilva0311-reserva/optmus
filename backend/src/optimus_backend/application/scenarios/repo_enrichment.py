import json
from dataclasses import dataclass

from optimus_backend.application.scenarios.repo_ranking import RankedCandidate, rank_candidates
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
    ranking_preview: list[dict[str, object]]
    skipped_reason: str | None = None



def _repo_enrichment_enabled(inputs: dict[str, object]) -> bool:
    raw = inputs.get("repo_enrichment")
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, dict):
        return bool(raw.get("enabled"))
    return False



def _preview(candidates: list[RankedCandidate]) -> list[dict[str, object]]:
    return [
        {
            "path": item.path,
            "score": item.score,
            "reasons": item.reasons,
            "module_key": item.module_key,
        }
        for item in candidates[:5]
    ]


def _bug_diagnosis_pipeline(connector: SourceConnector, inputs: dict[str, object]) -> tuple[list[RankedCandidate], int]:
    file_pattern = str(inputs.get("file_pattern", "**/*")).strip() or "**/*"
    query_text = str(inputs.get("observed_error", "")).strip()
    listed_paths = connector.list_files(file_pattern)
    search_hits = connector.search(query_text) if query_text else []
    ranked = rank_candidates(
        paths=listed_paths,
        search_hits=search_hits,
        query_text=query_text,
        file_pattern=file_pattern,
        per_module_limit=2,
        max_results=config.repo_enrichment_max_files * 4,
    )
    return ranked, len(search_hits)


def _refactor_pipeline(connector: SourceConnector, inputs: dict[str, object]) -> tuple[list[RankedCandidate], int]:
    file_pattern = str(inputs.get("file_pattern", "**/*")).strip() or "**/*"
    query_text = str(inputs.get("objective", "")).strip()
    listed_paths = connector.list_files(file_pattern)
    search_hits = connector.search(query_text) if query_text else []
    ranked = rank_candidates(
        paths=listed_paths,
        search_hits=search_hits,
        query_text=query_text,
        file_pattern=file_pattern,
        per_module_limit=3,
        max_results=config.repo_enrichment_max_files * 4,
    )
    return ranked, len(search_hits)



def enrich_repo_inputs_for_scenario(
    scenario_id: str,
    inputs: dict[str, object],
    source_connector_factory: type[SourceConnector] | None,
) -> RepoEnrichmentOutcome:
    if scenario_id not in SUPPORTED_SCENARIOS:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, [], "scenario_not_supported")

    if source_connector_factory is None:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, [], "connector_unavailable")

    if "files" in inputs:
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, [], "files_already_provided")

    if not _repo_enrichment_enabled(inputs):
        return RepoEnrichmentOutcome(inputs, False, False, scenario_id, 0, 0, 0, [], "repo_enrichment_disabled")

    repo_path = str(inputs.get("repo_path", "")).strip()
    if not repo_path:
        return RepoEnrichmentOutcome(inputs, True, False, scenario_id, 0, 0, 0, [], "repo_path_missing")

    connector = source_connector_factory(repo_path)
    ranked_candidates, search_hits = (
        _bug_diagnosis_pipeline(connector, inputs)
        if scenario_id == "bug_diagnosis"
        else _refactor_pipeline(connector, inputs)
    )

    if len(ranked_candidates) > config.repo_enrichment_max_files:
        raise ValueError(
            f"repo enrichment exceeded max files: {len(ranked_candidates)} > {config.repo_enrichment_max_files}. "
            "Narrow file_pattern or provide files explicitly."
        )

    total_bytes = 0
    selected_files: list[dict[str, str]] = []
    for candidate in ranked_candidates:
        content = connector.fetch_file(candidate.path)
        content_bytes = len(content.encode("utf-8"))
        total_bytes += content_bytes
        if total_bytes > config.repo_enrichment_max_total_bytes:
            raise ValueError(
                f"repo enrichment exceeded total limit: {total_bytes} > {config.repo_enrichment_max_total_bytes} bytes. "
                "Narrow file_pattern or provide files explicitly."
            )
        selected_files.append({"path": candidate.path, "content": content})

    enriched = dict(inputs)
    enriched["files"] = selected_files
    return RepoEnrichmentOutcome(
        inputs=enriched,
        attempted=True,
        applied=True,
        scenario_id=scenario_id,
        listed_files=len(ranked_candidates),
        selected_files=len(selected_files),
        search_hits=search_hits,
        ranking_preview=_preview(ranked_candidates),
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
        "ranking_preview": outcome.ranking_preview,
        "skipped_reason": outcome.skipped_reason,
    }
    return json.dumps(payload, sort_keys=True)
