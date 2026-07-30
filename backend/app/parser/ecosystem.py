"""Framework/ecosystem detection from dependency manifests.

Deliberately manifest-driven rather than import-sniffing: it's far more
reliable ("react" in package.json dependencies beats guessing from JSX
syntax) and covers every framework named in the product brief.
"""

import json
import re
import tomllib
from dataclasses import dataclass

from app.ingest.files import FileRecord, read_text_safe

# framework name -> (manifest filename, dependency keys to look for)
_NODE_FRAMEWORK_PACKAGES = {
    "react": "react",
    "next.js": "next",
    "angular": "@angular/core",
    "vue": "vue",
    "express": "express",
    "nestjs": "@nestjs/core",
    "svelte": "svelte",
}

_PYTHON_FRAMEWORK_PACKAGES = {
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
}


@dataclass(slots=True)
class EcosystemInfo:
    frameworks: list[str]
    package_managers: list[str]


def detect_ecosystem(file_records: list[FileRecord]) -> EcosystemInfo:
    # Keyed by basename (not full path) so this also picks up manifests nested
    # in monorepo sub-projects (frontend/package.json, backend/pyproject.toml, ...).
    by_name = {f.relative_path.rsplit("/", 1)[-1]: f for f in file_records}
    frameworks: set[str] = set()
    package_managers: set[str] = set()

    if "package.json" in by_name:
        package_managers.add("npm/yarn/pnpm")
        frameworks |= _detect_node_frameworks(by_name["package.json"])

    if "requirements.txt" in by_name:
        package_managers.add("pip")
        frameworks |= _detect_python_frameworks_text(by_name["requirements.txt"])

    if "pyproject.toml" in by_name:
        package_managers.add("poetry/pip")
        frameworks |= _detect_python_frameworks_toml(by_name["pyproject.toml"])

    if "pom.xml" in by_name:
        package_managers.add("maven")
        if _contains(by_name["pom.xml"], "spring-boot"):
            frameworks.add("spring boot")

    for gradle_name in ("build.gradle", "build.gradle.kts"):
        if gradle_name in by_name:
            package_managers.add("gradle")
            if _contains(by_name[gradle_name], "spring-boot"):
                frameworks.add("spring boot")

    if "composer.json" in by_name:
        package_managers.add("composer")
        frameworks |= _detect_composer_frameworks(by_name["composer.json"])

    if "go.mod" in by_name:
        package_managers.add("go modules")

    if "cargo.toml" in {n.lower() for n in by_name}:
        package_managers.add("cargo")

    if "gemfile" in {n.lower() for n in by_name}:
        package_managers.add("bundler")
        gemfile = by_name.get("Gemfile") or by_name.get("gemfile")
        if gemfile and _contains(gemfile, "rails"):
            frameworks.add("rails")

    return EcosystemInfo(frameworks=sorted(frameworks), package_managers=sorted(package_managers))


def _contains(record: FileRecord, needle: str) -> bool:
    content = read_text_safe(record.absolute_path)
    if content is None:
        return False
    return needle.lower() in content.lower()


def _detect_node_frameworks(record: FileRecord) -> set[str]:
    content = read_text_safe(record.absolute_path)
    if not content:
        return set()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return set()
    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return {name for name, pkg in _NODE_FRAMEWORK_PACKAGES.items() if pkg in deps}


def _detect_python_frameworks_text(record: FileRecord) -> set[str]:
    content = (read_text_safe(record.absolute_path) or "").lower()
    lines = {re.split(r"[=<>~\[; ]", line.strip())[0] for line in content.splitlines() if line.strip()}
    return {name for name, pkg in _PYTHON_FRAMEWORK_PACKAGES.items() if pkg in lines}


def _detect_python_frameworks_toml(record: FileRecord) -> set[str]:
    content = read_text_safe(record.absolute_path)
    if not content:
        return set()
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError:
        return set()
    deps: set[str] = set()
    project_deps = data.get("project", {}).get("dependencies", [])
    deps |= {re.split(r"[=<>~\[; ]", d.strip())[0].lower() for d in project_deps}
    poetry_deps = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    deps |= {k.lower() for k in poetry_deps}
    return {name for name, pkg in _PYTHON_FRAMEWORK_PACKAGES.items() if pkg in deps}


def _detect_composer_frameworks(record: FileRecord) -> set[str]:
    content = read_text_safe(record.absolute_path)
    if not content:
        return set()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return set()
    deps = {**data.get("require", {}), **data.get("require-dev", {})}
    frameworks = set()
    if any("laravel/framework" in k for k in deps):
        frameworks.add("laravel")
    if any(k.startswith("symfony/") for k in deps):
        frameworks.add("symfony")
    return frameworks
