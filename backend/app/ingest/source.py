"""Materialize a repository (git URL, uploaded ZIP, or local path) onto disk
as a plain directory tree that the rest of the pipeline can read uniformly."""

import shutil
import zipfile
from pathlib import Path

import git

from app.core.exceptions import RepoIngestError


def clone_git_repo(url: str, workspace: Path) -> Path:
    dest = workspace / "repo"
    try:
        git.Repo.clone_from(url, dest, depth=1, single_branch=True)
    except git.GitError as exc:
        raise RepoIngestError(f"Failed to clone repository: {exc}") from exc
    return dest


def extract_zip(zip_path: Path, workspace: Path) -> Path:
    dest = workspace / "repo"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path) as zf:
            _safe_extract(zf, dest)
    except zipfile.BadZipFile as exc:
        raise RepoIngestError(f"Not a valid ZIP file: {exc}") from exc

    # Many ZIP exports wrap everything in a single top-level folder
    # (GitHub's "Download ZIP" does this) — flatten it so paths are clean.
    entries = list(dest.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for child in inner.iterdir():
            shutil.move(str(child), str(dest / child.name))
        inner.rmdir()

    return dest


def _safe_extract(zf: zipfile.ZipFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in zf.infolist():
        member_path = (dest / member.filename).resolve()
        if not str(member_path).startswith(str(dest_resolved)):
            raise RepoIngestError(f"Unsafe path in ZIP archive: {member.filename}")
    zf.extractall(dest)


def prepare_local(path_str: str) -> Path:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise RepoIngestError(f"Local path does not exist: {path}")
    if not path.is_dir():
        raise RepoIngestError(f"Local path is not a directory: {path}")
    return path
