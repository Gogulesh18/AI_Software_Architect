"""Architecture style classification with a confidence score.

Signal-based, not a single rule: each candidate style accumulates weighted
points from folder-name/file/ecosystem signals actually observed in the
repo. The highest-scoring style wins; its score relative to the max
possible for that style becomes the confidence (0-100). Every matched
signal is kept as "evidence" so the report can explain *why*.
"""

from dataclasses import dataclass
from typing import Any

from app.graph.summary import RepoSummary
from app.parser.models import ParsedFile


@dataclass(slots=True)
class _Signal:
    weight: int
    description: str
    matched: bool


def _folder_names(parsed_files: list[ParsedFile]) -> set[str]:
    names: set[str] = set()
    for pf in parsed_files:
        parts = pf.relative_path.split("/")[:-1]
        names.update(p.lower() for p in parts)
    return names


def _file_basenames(parsed_files: list[ParsedFile]) -> set[str]:
    return {pf.relative_path.rsplit("/", 1)[-1].lower() for pf in parsed_files}


def _has_any(haystack: set[str], *needles: str) -> bool:
    return any(n in haystack for n in needles)


def detect_architecture(parsed_files: list[ParsedFile], summary: RepoSummary) -> dict:
    folders = _folder_names(parsed_files)
    files = _file_basenames(parsed_files)
    top_level_dirs = {pf.relative_path.split("/")[0] for pf in parsed_files if "/" in pf.relative_path}

    manifest_names = {"package.json", "pyproject.toml", "pom.xml", "build.gradle", "go.mod", "cargo.toml", "composer.json"}
    services_with_own_manifest = 0
    for top in top_level_dirs:
        prefix = f"{top}/"
        has_manifest = any(
            pf.relative_path.startswith(prefix) and pf.relative_path.rsplit("/", 1)[-1].lower() in manifest_names
            for pf in parsed_files
        )
        if has_manifest:
            services_with_own_manifest += 1

    dockerfiles = sum(1 for pf in parsed_files if pf.relative_path.rsplit("/", 1)[-1] == "Dockerfile")
    all_imports = {raw.lower() for pf in parsed_files for raw in pf.imports}
    has_message_broker_dep = _has_any(
        all_imports, "kafka", "pika", "aio_pika", "confluent_kafka", "amqplib", "kafkajs"
    )

    candidates: dict[str, list[_Signal]] = {
        "Microservices": [
            _Signal(4, "multiple top-level sub-projects with their own manifest", services_with_own_manifest >= 2),
            _Signal(3, "multiple Dockerfiles at different paths", dockerfiles >= 2),
            _Signal(2, "docker-compose defines the deployment topology", "docker-compose.yml" in files or "docker-compose.yaml" in files),
        ],
        "Serverless": [
            _Signal(4, "serverless.yml present", "serverless.yml" in files),
            _Signal(3, "SAM/CloudFormation template present", _has_any(files, "template.yaml", "template.yml")),
            _Signal(2, "handler-style entrypoint file(s)", _has_any(files, "handler.py", "lambda_function.py", "index.mjs")),
        ],
        "Hexagonal": [
            _Signal(4, "ports/adapters folders present", _has_any(folders, "ports", "adapters")),
            _Signal(3, "domain + infrastructure separation", _has_any(folders, "domain") and _has_any(folders, "infrastructure", "infra")),
        ],
        "Clean Architecture": [
            _Signal(4, "domain/application/infrastructure layering", _has_any(folders, "domain") and _has_any(folders, "application") and _has_any(folders, "infrastructure")),
            _Signal(2, "usecases folder present", _has_any(folders, "usecases", "use_cases")),
        ],
        "Event-Driven": [
            _Signal(4, "producer/consumer or queue-oriented folders", _has_any(folders, "consumers", "producers", "handlers", "subscribers")),
            _Signal(3, "message broker dependency", has_message_broker_dep),
        ],
        "Layered": [
            _Signal(3, "controller/service/repository layering", _has_any(folders, "controllers", "controller") and _has_any(folders, "services", "service")),
            _Signal(2, "repository layer present", _has_any(folders, "repositories", "repository", "dao")),
        ],
        "MVC": [
            _Signal(4, "models/views/controllers folders present", _has_any(folders, "models", "model") and _has_any(folders, "views", "view") and _has_any(folders, "controllers", "controller")),
            _Signal(2, "Django-style app module (models.py + views.py + urls.py)", _has_any(files, "models.py") and _has_any(files, "views.py") and _has_any(files, "urls.py")),
        ],
        "Monolith": [
            _Signal(2, "single top-level application, no service split", services_with_own_manifest <= 1),
            _Signal(1, "no deployment-topology signals found", dockerfiles <= 1 and "docker-compose.yml" not in files),
        ],
    }

    scored: list[dict[str, Any]] = []
    for style, signals in candidates.items():
        matched = [s for s in signals if s.matched]
        max_possible = sum(s.weight for s in signals)
        raw = sum(s.weight for s in matched)
        confidence = round(100 * raw / max_possible) if max_possible else 0
        scored.append(
            {
                "style": style,
                "confidence": confidence,
                "evidence": [s.description for s in matched],
            }
        )

    scored.sort(key=lambda s: s["confidence"], reverse=True)

    # Monolith has so few possible signals that it saturates to 100% on any
    # repo without a service split — that makes it an unfair "competitor" to
    # specific styles with more (harder to satisfy) signals. Treat it purely
    # as the fallback: only chosen when no specific style clears a minimum
    # confidence, never chosen just because its own bar is easy to clear.
    specific = [s for s in scored if s["style"] != "Monolith"]
    monolith = next(s for s in scored if s["style"] == "Monolith")
    best_specific = specific[0] if specific else None

    MIN_CONFIDENCE = 25
    best = best_specific if best_specific and best_specific["confidence"] >= MIN_CONFIDENCE else monolith

    return {
        "primary_style": best["style"],
        "confidence": best["confidence"],
        "evidence": best["evidence"],
        "all_candidates": scored,
    }
