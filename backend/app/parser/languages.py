"""Map file paths to a canonical language label.

Languages with an entry in app.parser.ts_specs.LANGUAGE_SPECS get full
Tree-sitter structural extraction (imports/classes/functions/complexity).
Everything else still gets a language label and is counted in the repo
summary / folder tree / dependency graph, just without deep AST extraction.
"""

from pathlib import PurePosixPath

_EXTENSION_MAP: dict[str, str] = {
    # deep-parsed languages
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".tsx": "tsx",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".c": "c",
    ".h": "c",
    # shallow (labeled, not AST-parsed)
    ".rb": "ruby",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".scala": "scala",
    ".html": "html",
    ".htm": "html",
    ".vue": "vue",
    ".svelte": "svelte",
    ".css": "css",
    ".scss": "scss",
    ".sass": "scss",
    ".less": "less",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".md": "markdown",
    ".mdx": "markdown",
    ".xml": "xml",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".proto": "protobuf",
    ".r": "r",
    ".dart": "dart",
    ".lua": "lua",
    ".pl": "perl",
    ".hs": "haskell",
    ".ex": "elixir",
    ".exs": "elixir",
    ".clj": "clojure",
    ".groovy": "groovy",
    ".gradle": "groovy",
}

_FILENAME_MAP: dict[str, str] = {
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
    "Jenkinsfile": "groovy",
    "Gemfile": "ruby",
    "Rakefile": "ruby",
    "Procfile": "yaml",
    "docker-compose.yml": "yaml",
    "docker-compose.yaml": "yaml",
}

# Languages with a matching LanguageSpec in app.parser.ts_specs — deep AST extraction applies.
DEEP_PARSE_LANGUAGES: frozenset[str] = frozenset(
    {"python", "javascript", "typescript", "tsx", "java", "go", "rust", "php", "csharp", "cpp", "c"}
)


def detect_language(relative_path: str) -> str:
    name = PurePosixPath(relative_path).name
    if name in _FILENAME_MAP:
        return _FILENAME_MAP[name]

    suffix = PurePosixPath(relative_path).suffix.lower()
    return _EXTENSION_MAP.get(suffix, "other")
