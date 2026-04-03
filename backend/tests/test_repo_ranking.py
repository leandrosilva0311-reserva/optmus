from optimus_backend.application.scenarios.repo_ranking import rank_candidates, score_candidate


def test_score_candidate_returns_score_and_reasons() -> None:
    ranked = score_candidate(
        path="services/api/error_handler.py",
        query_text="ValueError invalid id",
        search_hit_count=2,
        file_pattern="**/*.py",
    )

    assert ranked.score > 0
    assert ranked.reasons
    assert any("search_hits" in reason for reason in ranked.reasons)


def test_rank_candidates_enforces_module_diversity() -> None:
    paths = [
        "services/api/error_handler.py",
        "services/api/error_utils.py",
        "services/core/validation.py",
        "frontend/src/app.tsx",
    ]
    search_hits = [
        {"path": "services/api/error_handler.py"},
        {"path": "services/api/error_utils.py"},
        {"path": "services/core/validation.py"},
        {"path": "services/core/validation.py"},
    ]

    ranked = rank_candidates(
        paths=paths,
        search_hits=search_hits,
        query_text="error validation",
        file_pattern="**/*.py",
        per_module_limit=1,
        max_results=10,
    )

    assert ranked
    modules = [item.module_key for item in ranked]
    assert modules.count("services") == 1
