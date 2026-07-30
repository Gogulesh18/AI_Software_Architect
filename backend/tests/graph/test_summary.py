from app.graph.summary import compute_summary
from app.parser.ecosystem import EcosystemInfo
from app.parser.extractor import parse_source


def test_summary_totals_and_primary_language():
    files = [
        parse_source("app/main.py", "python", "def main():\n    pass\n"),
        parse_source("app/utils.py", "python", "def helper():\n    pass\n"),
        parse_source("README.md", "markdown", "# Title\n"),
    ]
    ecosystem = EcosystemInfo(frameworks=["fastapi"], package_managers=["pip"])

    summary = compute_summary(files, ecosystem)

    assert summary.total_files == 3
    assert summary.primary_language == "python"
    assert summary.languages["python"]["files"] == 2
    assert summary.frameworks == ["fastapi"]


def test_folder_tree_nests_correctly():
    files = [
        parse_source("app/api/routes.py", "python", "x = 1\n"),
        parse_source("app/core/config.py", "python", "x = 1\n"),
        parse_source("README.md", "markdown", "# hi\n"),
    ]
    summary = compute_summary(files, EcosystemInfo(frameworks=[], package_managers=[]))

    tree = summary.folder_tree
    assert tree["type"] == "dir"
    names = {c["name"] for c in tree["children"]}
    assert names == {"app", "README.md"}

    app_node = next(c for c in tree["children"] if c["name"] == "app")
    assert app_node["file_count"] == 2
    sub_names = {c["name"] for c in app_node["children"]}
    assert sub_names == {"api", "core"}
