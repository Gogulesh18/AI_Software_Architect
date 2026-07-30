"""Tree-sitter based structural extraction for the "deep parse" languages."""

import logging

from tree_sitter import Node
from tree_sitter_language_pack import get_parser

from app.parser.models import ParsedFile, ParsedSymbol
from app.parser.ts_specs import LANGUAGE_SPECS, LanguageSpec

logger = logging.getLogger(__name__)

_PARSER_CACHE: dict[str, object] = {}


def _get_parser(ts_name: str):
    if ts_name not in _PARSER_CACHE:
        _PARSER_CACHE[ts_name] = get_parser(ts_name)
    return _PARSER_CACHE[ts_name]


def parse_source(relative_path: str, language: str, source: str) -> ParsedFile:
    loc = len(source.splitlines())
    spec = LANGUAGE_SPECS.get(language)
    if spec is None:
        return ParsedFile(relative_path=relative_path, language=language, loc=loc, source=source)

    src_bytes = source.encode("utf-8", errors="replace")
    try:
        parser = _get_parser(spec.ts_name)
        tree = parser.parse(src_bytes)
    except Exception as exc:  # noqa: BLE001 - pragma: no cover - defensive, grammar/runtime failures
        logger.warning("Tree-sitter parse failed for %s: %s", relative_path, exc)
        return ParsedFile(
            relative_path=relative_path, language=language, loc=loc, parse_error=str(exc), source=source
        )

    imports = _extract_imports(tree.root_node, spec, src_bytes)
    symbols = _extract_symbols(tree.root_node, spec, src_bytes)

    return ParsedFile(
        relative_path=relative_path,
        language=language,
        loc=loc,
        imports=imports,
        symbols=symbols,
        source=source,
    )


def _text(node: Node, src: bytes) -> str:
    return src[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _extract_imports(root: Node, spec: LanguageSpec, src: bytes) -> list[str]:
    imports: list[str] = []

    def walk(node: Node) -> None:
        if node.type in spec.import_nodes:
            imports.append(_summarize_import(node, src))
            return  # don't descend into an import statement's own children
        for child in node.children:
            walk(child)

    walk(root)
    return imports


def _summarize_import(node: Node, src: bytes) -> str:
    # Prefer a string literal (require("x"), #include <x>, Go's import "fmt")
    # or dotted name/identifier descendant over the raw statement text —
    # cleaner for the dependency graph. Searches descendants, not just direct
    # children: e.g. Go nests the string two levels down (import_spec -> string).
    for child in _descendants(node):
        if child.type in ("string", "string_literal", "interpreted_string_literal", "system_lib_string"):
            return _text(child, src).strip("\"'<>")
    for child in _descendants(node):
        if child.type in ("dotted_name", "identifier", "qualified_identifier", "scoped_identifier"):
            return _text(child, src)
    return _text(node, src).strip().rstrip(";")


def _descendants(node: Node):
    for child in node.children:
        yield child
        yield from _descendants(child)


def _extract_symbols(root: Node, spec: LanguageSpec, src: bytes) -> list[ParsedSymbol]:
    symbols: list[ParsedSymbol] = []

    def walk(node: Node, parent_class: str | None) -> None:
        if node.type in spec.class_nodes:
            name = _node_name(node, src) or "<anonymous>"
            symbols.append(
                ParsedSymbol(
                    kind="class",
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    decorators=_preceding_decorators(node, spec, src),
                    parent_class=parent_class,
                    base_classes=_base_classes(node, spec.ts_name, src),
                )
            )
            for child in node.children:
                walk(child, parent_class=name)
            return

        if node.type in spec.function_nodes:
            name = _node_name(node, src) or "<anonymous>"
            symbols.append(
                ParsedSymbol(
                    kind="method" if parent_class else "function",
                    name=name,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    decorators=_preceding_decorators(node, spec, src),
                    calls=_calls_within(node, spec, src),
                    complexity=_complexity_within(node, spec),
                    max_nesting_depth=_max_nesting_depth_within(node, spec),
                    max_loop_nesting=_max_depth_for(node, spec.loop_nodes),
                    parent_class=parent_class,
                )
            )
            # Don't recurse into a function body for further class/function
            # nodes here — nested/local functions are rare enough across
            # these languages that flattening them one level up is fine.
            return

        for child in node.children:
            walk(child, parent_class)

    walk(root, None)
    return symbols


def _node_name(node: Node, src: bytes) -> str | None:
    name_field = node.child_by_field_name("name")
    if name_field is not None:
        return _text(name_field, src)

    # Go: `type_declaration` has no name field of its own — the identifier is
    # one level down, on its `type_spec` child.
    if node.type == "type_declaration":
        for child in node.children:
            if child.type == "type_spec":
                spec_name = child.child_by_field_name("name")
                if spec_name is not None:
                    return _text(spec_name, src)

    # C/C++: name lives at the bottom of a chain of `declarator` fields.
    declarator = node.child_by_field_name("declarator")
    seen = 0
    while declarator is not None and seen < 8:
        if declarator.type in ("identifier", "field_identifier", "qualified_identifier"):
            return _text(declarator, src)
        declarator = declarator.child_by_field_name("declarator")
        seen += 1
    return None


# Node types that wrap a decorator/annotation without being one themselves
# (Java nests @Annotation inside `modifiers`; PHP nests #[Attr] inside
# `attribute_list` -> `attribute_group`). Harmless to check for every language.
_DECORATOR_WRAPPER_NODES = frozenset({"modifiers", "attribute_list"})


def _preceding_decorators(node: Node, spec: LanguageSpec, src: bytes) -> list[str]:
    if not spec.decorator_nodes:
        return []

    decorators: list[str] = []

    # Case A: decorator/attribute is a direct child of the node itself, maybe
    # nested one level inside a wrapper (Java `modifiers`, C# `attribute_list`,
    # PHP `attribute_list -> attribute_group`, TS class decorators).
    for child in node.children:
        if child.type in spec.decorator_nodes:
            decorators.append(_text(child, src).strip())
        elif child.type in _DECORATOR_WRAPPER_NODES:
            for descendant in _descendants(child):
                if descendant.type in spec.decorator_nodes:
                    decorators.append(_text(descendant, src).strip())

    # Case B: decorator is a preceding sibling of the node (Python wraps
    # def/class + its decorators in `decorated_definition`; JS/TS method
    # decorators precede the method inside `class_body`).
    sibling = node.prev_sibling
    while sibling is not None and sibling.type in spec.decorator_nodes:
        decorators.insert(0, _text(sibling, src).strip())
        sibling = sibling.prev_sibling

    return decorators


_IDENTIFIER_LEAF_TYPES = frozenset({"identifier", "type_identifier", "name", "qualified_identifier"})


def _collect_identifier_texts(container: Node, src: bytes) -> list[str]:
    return [_text(n, src) for n in _descendants(container) if n.type in _IDENTIFIER_LEAF_TYPES]


def _find_child_by_type(node: Node, type_name: str) -> Node | None:
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _base_classes(node: Node, ts_name: str, src: bytes) -> list[str]:
    """Extract extends/implements targets. Field names verified per-grammar
    (Python's `superclasses`, Java's `superclass`/`interfaces`, etc.) — a
    blind generic node-type scan would false-positive on e.g. Python call
    argument lists, which share a node type with its superclass list."""
    names: list[str] = []

    if ts_name == "python":
        args = node.child_by_field_name("superclasses")
        if args is not None:
            names += _collect_identifier_texts(args, src)
    elif ts_name in ("javascript", "typescript", "tsx"):
        heritage = _find_child_by_type(node, "class_heritage")
        if heritage is not None:
            names += _collect_identifier_texts(heritage, src)
    elif ts_name == "java":
        superclass = node.child_by_field_name("superclass")
        if superclass is not None:
            names += _collect_identifier_texts(superclass, src)
        interfaces = node.child_by_field_name("interfaces")
        if interfaces is not None:
            names += _collect_identifier_texts(interfaces, src)
    elif ts_name == "csharp":
        base_list = _find_child_by_type(node, "base_list")
        if base_list is not None:
            names += _collect_identifier_texts(base_list, src)
    elif ts_name == "php":
        base_clause = _find_child_by_type(node, "base_clause")
        if base_clause is not None:
            names += _collect_identifier_texts(base_clause, src)
        iface_clause = _find_child_by_type(node, "class_interface_clause")
        if iface_clause is not None:
            names += _collect_identifier_texts(iface_clause, src)
    elif ts_name in ("cpp", "c"):
        base_clause = _find_child_by_type(node, "base_class_clause")
        if base_clause is not None:
            names += _collect_identifier_texts(base_clause, src)

    return names


def _calls_within(node: Node, spec: LanguageSpec, src: bytes) -> list[str]:
    calls: list[str] = []
    for descendant in _descendants(node):
        if descendant.type in spec.call_nodes:
            callee = descendant.child_by_field_name("function") or descendant.child_by_field_name("type")
            calls.append(_text(callee, src) if callee is not None else _text(descendant, src)[:60])
    return calls[:200]  # cap: pathological files shouldn't blow up downstream analysis


def _complexity_within(node: Node, spec: LanguageSpec) -> int:
    complexity = 1
    for descendant in _descendants(node):
        if descendant.type in spec.branch_nodes:
            complexity += 1
    return complexity


def _max_nesting_depth_within(node: Node, spec: LanguageSpec) -> int:
    return _max_depth_for(node, spec.branch_nodes)


def _max_depth_for(node: Node, node_types: frozenset[str]) -> int:
    def depth(n: Node, current: int) -> int:
        next_depth = current + 1 if n.type in node_types else current
        best = next_depth
        for child in n.children:
            best = max(best, depth(child, next_depth))
        return best

    return depth(node, 0)
