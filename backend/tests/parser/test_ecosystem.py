import json

from app.ingest.files import FileRecord
from app.parser.ecosystem import detect_ecosystem


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return FileRecord(relative_path=name, absolute_path=path, size_bytes=path.stat().st_size)


def test_detects_react_and_express_from_package_json(tmp_path):
    pkg = json.dumps({"dependencies": {"react": "^18.0.0", "express": "^4.0.0"}})
    record = _write(tmp_path, "package.json", pkg)

    info = detect_ecosystem([record])

    assert "react" in info.frameworks
    assert "express" in info.frameworks
    assert "npm/yarn/pnpm" in info.package_managers


def test_detects_fastapi_from_pyproject_toml(tmp_path):
    content = """
[project]
dependencies = ["fastapi>=0.115", "uvicorn"]
"""
    record = _write(tmp_path, "pyproject.toml", content)

    info = detect_ecosystem([record])

    assert "fastapi" in info.frameworks


def test_detects_spring_boot_from_pom_xml(tmp_path):
    record = _write(tmp_path, "pom.xml", "<project><dependency>spring-boot-starter-web</dependency></project>")

    info = detect_ecosystem([record])

    assert "spring boot" in info.frameworks
    assert "maven" in info.package_managers


def test_detects_laravel_from_composer_json(tmp_path):
    content = json.dumps({"require": {"laravel/framework": "^10.0"}})
    record = _write(tmp_path, "composer.json", content)

    info = detect_ecosystem([record])

    assert "laravel" in info.frameworks


def test_no_manifests_returns_empty(tmp_path):
    info = detect_ecosystem([])
    assert info.frameworks == []
    assert info.package_managers == []
