"""Directories/files skipped during ingestion — dependency and build output, not source."""

IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {
        # explicitly called out in the product brief
        "node_modules",
        "build",
        "dist",
        "target",
        "bin",
        "vendor",
        ".venv",
        "__pycache__",
        # version control / editor / tooling
        ".git",
        ".hg",
        ".svn",
        ".idea",
        ".vscode",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "venv",
        "env",
        # per-ecosystem build/dependency output not already covered above
        ".next",
        ".nuxt",
        ".angular",
        "coverage",
        ".gradle",
        ".mvn",
        "obj",  # .NET intermediate output
        "Pods",  # CocoaPods
        ".terraform",
        "site-packages",
        "egg-info",
        ".cache",
        ".parcel-cache",
        ".serverless",
        ".dart_tool",
        "bower_components",
    }
)

IGNORED_FILE_SUFFIXES: frozenset[str] = frozenset(
    {
        ".min.js",
        ".min.css",
        ".map",
        ".lock",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".webp",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".7z",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".pyc",
        ".class",
        ".jar",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".db",
        ".sqlite3",
    }
)

IGNORED_FILE_NAMES: frozenset[str] = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
    }
)


def is_ignored_dir(dir_name: str) -> bool:
    # Note: NOT a blanket "skip all dot-dirs" rule — .github/.gitlab-ci etc. are kept
    # so deployment/CI diagrams can pick up workflow and pipeline config.
    return dir_name in IGNORED_DIR_NAMES


def is_ignored_file(file_name: str) -> bool:
    if file_name in IGNORED_FILE_NAMES:
        return True
    lower = file_name.lower()
    return any(lower.endswith(suffix) for suffix in IGNORED_FILE_SUFFIXES)
