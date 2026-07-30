"""Build a NetworkX knowledge graph from parsed files.

Nodes: file, class, function, method, external_package.
Edges: imports (file->file | file->external_package), defines (file->symbol,
class->method), inherits (class->class, resolved only), calls (function-like
-> function-like, resolved only).

Import/call/base-class resolution is heuristic (string/name matching, not a
real per-language module resolver) — accurate enough to drive dependency
diagrams and pattern/SOLID heuristics, not a compiler. Ambiguous references
(name matches >1 candidate) are left unresolved rather than guessed, so the
graph doesn't accumulate wrong edges.
"""

import posixpath

import networkx as nx

from app.parser.models import ParsedFile


def symbol_id(file_path: str, symbol_name: str, parent_class: str | None = None) -> str:
    if parent_class:
        return f"{file_path}::{parent_class}.{symbol_name}"
    return f"{file_path}::{symbol_name}"


def build_graph(parsed_files: list[ParsedFile]) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    _add_file_and_symbol_nodes(graph, parsed_files)
    _add_import_edges(graph, parsed_files)
    _add_inherits_edges(graph, parsed_files)
    _add_calls_edges(graph, parsed_files)

    return graph


def _add_file_and_symbol_nodes(graph: nx.MultiDiGraph, parsed_files: list[ParsedFile]) -> None:
    for pf in parsed_files:
        graph.add_node(
            pf.relative_path,
            type="file",
            language=pf.language,
            loc=pf.loc,
            num_classes=len(pf.classes),
            num_functions=len(pf.functions),
            parse_error=pf.parse_error,
        )

        for cls in pf.classes:
            cls_id = symbol_id(pf.relative_path, cls.name)
            graph.add_node(
                cls_id,
                type="class",
                name=cls.name,
                file=pf.relative_path,
                language=pf.language,
                start_line=cls.start_line,
                end_line=cls.end_line,
                loc=max(cls.end_line - cls.start_line + 1, 1),
                decorators=cls.decorators,
                base_classes=cls.base_classes,
            )
            graph.add_edge(pf.relative_path, cls_id, type="defines")

        for func in pf.functions:
            func_id = symbol_id(pf.relative_path, func.name, func.parent_class)
            graph.add_node(
                func_id,
                type="method" if func.parent_class else "function",
                name=func.name,
                file=pf.relative_path,
                language=pf.language,
                start_line=func.start_line,
                end_line=func.end_line,
                loc=max(func.end_line - func.start_line + 1, 1),
                complexity=func.complexity,
                decorators=func.decorators,
                parent_class=func.parent_class,
            )
            owner = symbol_id(pf.relative_path, func.parent_class) if func.parent_class else pf.relative_path
            if graph.has_node(owner):
                graph.add_edge(owner, func_id, type="defines")


def _add_import_edges(graph: nx.MultiDiGraph, parsed_files: list[ParsedFile]) -> None:
    all_paths = [pf.relative_path for pf in parsed_files]
    resolver = _FileResolver(all_paths)

    for pf in parsed_files:
        for raw_import in pf.imports:
            target = resolver.resolve(pf.relative_path, raw_import)
            if target is not None:
                graph.add_edge(pf.relative_path, target, type="imports", raw=raw_import)
            else:
                package_root = _package_root(raw_import)
                ext_id = f"external::{package_root}"
                if not graph.has_node(ext_id):
                    graph.add_node(ext_id, type="external_package", name=package_root)
                graph.add_edge(pf.relative_path, ext_id, type="imports", raw=raw_import)


def _add_inherits_edges(graph: nx.MultiDiGraph, parsed_files: list[ParsedFile]) -> None:
    by_name: dict[str, list[str]] = {}
    for pf in parsed_files:
        for cls in pf.classes:
            by_name.setdefault(cls.name, []).append(symbol_id(pf.relative_path, cls.name))

    for pf in parsed_files:
        for cls in pf.classes:
            cls_id = symbol_id(pf.relative_path, cls.name)
            for base in cls.base_classes:
                base_short = base.rsplit(".", 1)[-1]
                candidates = by_name.get(base_short, [])
                if len(candidates) == 1 and candidates[0] != cls_id:
                    graph.add_edge(cls_id, candidates[0], type="inherits")


def _add_calls_edges(graph: nx.MultiDiGraph, parsed_files: list[ParsedFile]) -> None:
    by_name: dict[str, list[str]] = {}
    for pf in parsed_files:
        for func in pf.functions:
            by_name.setdefault(func.name, []).append(symbol_id(pf.relative_path, func.name, func.parent_class))

    for pf in parsed_files:
        for func in pf.functions:
            caller_id = symbol_id(pf.relative_path, func.name, func.parent_class)
            for raw_call in func.calls:
                callee_short = raw_call.rsplit(".", 1)[-1]
                candidates = by_name.get(callee_short, [])
                if len(candidates) == 1 and candidates[0] != caller_id:
                    graph.add_edge(caller_id, candidates[0], type="calls")


def _package_root(raw_import: str) -> str:
    cleaned = raw_import.strip("./ ")
    if not cleaned:
        return raw_import
    first = cleaned.split("/")[0]
    if first.startswith("@") and "/" in cleaned:  # scoped npm package, e.g. @nestjs/common
        parts = cleaned.split("/")
        return "/".join(parts[:2])
    return first.split(".")[0] if "." in first and "/" not in cleaned else first


class _FileResolver:
    """Best-effort raw-import-string -> repo file path resolver.

    Not a real per-language module resolver (no tsconfig paths, no Go module
    proxy, no Maven coordinates) — matches relative paths exactly and falls
    back to a unique last-segment/basename match everywhere else. Ambiguous
    or unmatched imports are left unresolved (become external_package nodes)
    rather than guessed.
    """

    def __init__(self, all_paths: list[str]):
        self._all_paths = set(all_paths)
        self._by_stem: dict[str, list[str]] = {}
        for path in all_paths:
            stem = posixpath.splitext(posixpath.basename(path))[0]
            self._by_stem.setdefault(stem.lower(), []).append(path)

    def resolve(self, from_path: str, raw_import: str) -> str | None:
        if raw_import.startswith("."):
            resolved = self._resolve_relative(from_path, raw_import)
            if resolved:
                return resolved

        last_segment = raw_import.replace("\\", "/").split("/")[-1].split(".")[-1]
        candidates = self._by_stem.get(last_segment.lower(), [])
        if len(candidates) == 1:
            return candidates[0]
        return None

    def _resolve_relative(self, from_path: str, raw_import: str) -> str | None:
        base_dir = posixpath.dirname(from_path)
        target = posixpath.normpath(posixpath.join(base_dir, raw_import))
        candidates = [
            target,
            f"{target}.ts",
            f"{target}.tsx",
            f"{target}.js",
            f"{target}.jsx",
            f"{target}/index.ts",
            f"{target}/index.tsx",
            f"{target}/index.js",
        ]
        for candidate in candidates:
            if candidate in self._all_paths:
                return candidate
        return None
