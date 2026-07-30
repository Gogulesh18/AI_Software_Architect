import zipfile

import git
import pytest

from app.core.exceptions import RepoIngestError
from app.ingest.source import clone_git_repo, extract_zip, prepare_local


def test_extract_zip_normal_archive(tmp_path):
    zip_path = tmp_path / "repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("main.py", "print('hi')\n")
        zf.writestr("sub/util.py", "x = 1\n")

    dest = extract_zip(zip_path, tmp_path / "workspace")

    assert (dest / "main.py").read_text() == "print('hi')\n"
    assert (dest / "sub" / "util.py").exists()


def test_extract_zip_flattens_single_top_level_folder(tmp_path):
    # Mirrors GitHub's "Download ZIP", which wraps everything in
    # "<repo>-<branch>/" — extract_zip should strip that wrapper.
    zip_path = tmp_path / "repo.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("myrepo-main/README.md", "# hi\n")
        zf.writestr("myrepo-main/app/main.py", "x = 1\n")

    dest = extract_zip(zip_path, tmp_path / "workspace")

    assert (dest / "README.md").exists()
    assert (dest / "app" / "main.py").exists()
    assert not (dest / "myrepo-main").exists()


def test_extract_zip_rejects_path_traversal(tmp_path):
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../evil.txt", "pwned")

    with pytest.raises(RepoIngestError, match="Unsafe path"):
        extract_zip(zip_path, tmp_path / "workspace")


def test_extract_zip_rejects_bad_zip_file(tmp_path):
    bad_zip = tmp_path / "not_a_zip.zip"
    bad_zip.write_text("this is not a zip file")

    with pytest.raises(RepoIngestError, match="valid ZIP"):
        extract_zip(bad_zip, tmp_path / "workspace")


def test_prepare_local_rejects_missing_path(tmp_path):
    with pytest.raises(RepoIngestError, match="does not exist"):
        prepare_local(str(tmp_path / "nope"))


def test_prepare_local_rejects_file_not_directory(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hi")
    with pytest.raises(RepoIngestError, match="not a directory"):
        prepare_local(str(f))


def test_prepare_local_accepts_valid_directory(tmp_path):
    result = prepare_local(str(tmp_path))
    assert result == tmp_path.resolve()


def test_clone_git_repo_from_local_source(tmp_path):
    # Real GitPython clone against a local repo (file:// style path) —
    # exercises the actual clone path without needing network access.
    source_repo_path = tmp_path / "source_repo"
    source_repo_path.mkdir()
    source_repo = git.Repo.init(source_repo_path, initial_branch="main")
    (source_repo_path / "README.md").write_text("# hello\n")
    source_repo.index.add(["README.md"])
    source_repo.index.commit("initial commit")

    dest = clone_git_repo(str(source_repo_path), tmp_path / "workspace")

    assert (dest / "README.md").read_text() == "# hello\n"


def test_clone_git_repo_invalid_url_raises(tmp_path):
    with pytest.raises(RepoIngestError):
        clone_git_repo(str(tmp_path / "does-not-exist"), tmp_path / "workspace")
