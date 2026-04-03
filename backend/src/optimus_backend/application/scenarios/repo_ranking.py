from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

SCORE_WEIGHTS: dict[str, float] = {
    "search_hit": 3.0,
    "filename_token": 1.8,
    "path_token": 1.2,
    "pattern_match": 1.0,
    "preferred_extension": 0.5,
}

PREFERRED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    path: str
    score: float
    reasons: list[str]
    module_key: str


def _tokens(value: str) -> set[str]:
    clean = "".join(ch.lower() if ch.isalnum() else " " for ch in value)
    return {part for part in clean.split() if len(part) >= 3}


def _module_key(path: str) -> str:
    parts = Path(path).parts
    return parts[0] if parts else "root"


def score_candidate(path: str, query_text: str, search_hit_count: int, file_pattern: str) -> RankedCandidate:
    score = 0.0
    reasons: list[str] = []
    tokens = _tokens(query_text)
    filename = Path(path).name.lower()
    normalized_path = path.lower()

    if search_hit_count > 0:
        points = SCORE_WEIGHTS["search_hit"] * min(search_hit_count, 5)
        score += points
        reasons.append(f"search_hits:{search_hit_count} (+{points:.1f})")

    filename_tokens = sum(1 for token in tokens if token in filename)
    if filename_tokens:
        points = SCORE_WEIGHTS["filename_token"] * filename_tokens
        score += points
        reasons.append(f"filename_tokens:{filename_tokens} (+{points:.1f})")

    path_tokens = sum(1 for token in tokens if token in normalized_path)
    if path_tokens:
        points = SCORE_WEIGHTS["path_token"] * path_tokens
        score += points
        reasons.append(f"path_tokens:{path_tokens} (+{points:.1f})")

    if file_pattern and fnmatch(path, file_pattern):
        points = SCORE_WEIGHTS["pattern_match"]
        score += points
        reasons.append(f"pattern_match (+{points:.1f})")

    if Path(path).suffix.lower() in PREFERRED_EXTENSIONS:
        points = SCORE_WEIGHTS["preferred_extension"]
        score += points
        reasons.append(f"preferred_extension (+{points:.1f})")

    if not reasons:
        reasons.append("baseline")
    return RankedCandidate(path=path, score=round(score, 3), reasons=reasons, module_key=_module_key(path))


def rank_candidates(
    paths: list[str],
    search_hits: list[dict[str, object]],
    query_text: str,
    file_pattern: str,
    per_module_limit: int,
    max_results: int,
) -> list[RankedCandidate]:
    hit_counts: dict[str, int] = {}
    for hit in search_hits:
        path = str(hit.get("path", "")).strip()
        if not path:
            continue
        hit_counts[path] = hit_counts.get(path, 0) + 1

    scored = [score_candidate(path, query_text, hit_counts.get(path, 0), file_pattern) for path in paths]
    ordered = sorted(scored, key=lambda item: (-item.score, item.path))

    per_module: dict[str, int] = {}
    selected: list[RankedCandidate] = []
    for candidate in ordered:
        used = per_module.get(candidate.module_key, 0)
        if used >= per_module_limit:
            continue
        per_module[candidate.module_key] = used + 1
        selected.append(candidate)
        if len(selected) >= max_results:
            break
    return selected
