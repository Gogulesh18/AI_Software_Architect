"""Repository-level summary stats and folder tree, derived from parsed files."""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from app.parser.ecosystem import EcosystemInfo
from app.parser.models import ParsedFile


@dataclass(slots=True)
class RepoSummary:
    total_files: int
    total_loc: int
    languages: dict[str, dict[str, int]]  # language -> {"files": n, "loc": n}
    primary_language: str | None
    frameworks: list[str]
    package_managers: list[str]
    folder_tree: dict = field(default_factory=dict)


def compute_summary(parsed_files: list[ParsedFile], ecosystem: EcosystemInfo) -> RepoSummary:
    languages: dict[str, dict[str, int]] = defaultdict(lambda: {"files": 0, "loc": 0})
    for pf in parsed_files:
        languages[pf.language]["files"] += 1
        languages[pf.language]["loc"] += pf.loc

    code_languages = {
        lang: stats
        for lang, stats in languages.items()
        if lang not in ("json", "yaml", "markdown", "toml", "xml", "text", "other")
    }
    primary = max(code_languages, key=lambda lang: code_languages[lang]["loc"], default=None) if code_languages else None

    return RepoSummary(
        total_files=len(parsed_files),
        total_loc=sum(pf.loc for pf in parsed_files),
        languages=dict(languages),
        primary_language=primary,
        frameworks=ecosystem.frameworks,
        package_managers=ecosystem.package_managers,
        folder_tree=build_folder_tree(parsed_files),
    )


def build_folder_tree(parsed_files: list[ParsedFile]) -> dict:
    # Heterogeneous nested dict shape (str/int/dict/Counter values) built up
    # incrementally — typed loosely (dict[str, Any]) rather than a TypedDict,
    # since _finalize_tree flattens it into the real, precisely-typed
    # response shape right below.
    root: dict[str, Any] = {"name": "", "path": "", "type": "dir", "children": {}, "file_count": 0, "loc": 0, "languages": Counter()}

    for pf in parsed_files:
        parts = pf.relative_path.split("/")
        node: dict[str, Any] = root
        node["file_count"] += 1
        node["loc"] += pf.loc
        node["languages"][pf.language] += 1

        path_so_far = ""
        for part in parts[:-1]:
            path_so_far = f"{path_so_far}/{part}" if path_so_far else part
            child = node["children"].setdefault(
                part,
                {"name": part, "path": path_so_far, "type": "dir", "children": {}, "file_count": 0, "loc": 0, "languages": Counter()},
            )
            child["file_count"] += 1
            child["loc"] += pf.loc
            child["languages"][pf.language] += 1
            node = child

        file_name = parts[-1]
        node["children"][file_name] = {
            "name": file_name,
            "path": pf.relative_path,
            "type": "file",
            "language": pf.language,
            "loc": pf.loc,
        }

    return _finalize_tree(root)


def _finalize_tree(node: dict) -> dict:
    result = {
        "name": node["name"],
        "path": node["path"],
        "type": node["type"],
    }
    if node["type"] == "file":
        result["language"] = node["language"]
        result["loc"] = node["loc"]
        return result

    languages: Counter = node["languages"]
    result["file_count"] = node["file_count"]
    result["loc"] = node["loc"]
    result["primary_language"] = languages.most_common(1)[0][0] if languages else None
    result["children"] = [
        _finalize_tree(child) for _, child in sorted(node["children"].items(), key=lambda kv: (kv[1]["type"] != "dir", kv[0]))
    ]
    return result
