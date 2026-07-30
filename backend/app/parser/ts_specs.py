"""Per-language Tree-sitter node-type tables.

Grammars use different node type names for the same concept (an "import" is
`import_statement` in Python but `using_directive` in C#), so structural
extraction is driven by one small spec per language instead of bespoke
per-language parsing code. Verified against tree_sitter_language_pack's
actual grammars for each language listed here.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LanguageSpec:
    ts_name: str  # key passed to tree_sitter_language_pack.get_parser
    import_nodes: frozenset[str]
    class_nodes: frozenset[str]
    function_nodes: frozenset[str]
    call_nodes: frozenset[str]
    branch_nodes: frozenset[str]  # decision points, used for cyclomatic complexity
    loop_nodes: frozenset[str] = field(default_factory=frozenset)  # subset of branch_nodes; used for nested-loop perf checks
    decorator_nodes: frozenset[str] = field(default_factory=frozenset)
    # node type whose direct "name"-ish child holds the call's callee text
    call_text_node: str | None = None


PYTHON = LanguageSpec(
    ts_name="python",
    import_nodes=frozenset({"import_statement", "import_from_statement"}),
    class_nodes=frozenset({"class_definition"}),
    function_nodes=frozenset({"function_definition"}),
    call_nodes=frozenset({"call"}),
    branch_nodes=frozenset(
        {"if_statement", "elif_clause", "for_statement", "while_statement", "except_clause",
         "conditional_expression", "boolean_operator", "with_statement"}
    ),
    loop_nodes=frozenset({"for_statement", "while_statement"}),
    decorator_nodes=frozenset({"decorator"}),
)

JAVASCRIPT = LanguageSpec(
    ts_name="javascript",
    import_nodes=frozenset({"import_statement"}),
    class_nodes=frozenset({"class_declaration"}),
    function_nodes=frozenset(
        {"function_declaration", "method_definition", "arrow_function", "function_expression"}
    ),
    call_nodes=frozenset({"call_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "for_in_statement", "while_statement", "switch_case",
         "catch_clause", "ternary_expression", "binary_expression"}
    ),
    loop_nodes=frozenset({"for_statement", "for_in_statement", "while_statement"}),
    decorator_nodes=frozenset({"decorator"}),
)

TYPESCRIPT = LanguageSpec(
    ts_name="typescript",
    import_nodes=JAVASCRIPT.import_nodes,
    class_nodes=frozenset({"class_declaration", "interface_declaration"}),
    function_nodes=JAVASCRIPT.function_nodes,
    call_nodes=JAVASCRIPT.call_nodes,
    branch_nodes=JAVASCRIPT.branch_nodes,
    loop_nodes=JAVASCRIPT.loop_nodes,
    decorator_nodes=frozenset({"decorator"}),
)

TSX = LanguageSpec(
    ts_name="tsx",
    import_nodes=TYPESCRIPT.import_nodes,
    class_nodes=TYPESCRIPT.class_nodes,
    function_nodes=TYPESCRIPT.function_nodes,
    call_nodes=TYPESCRIPT.call_nodes,
    branch_nodes=TYPESCRIPT.branch_nodes,
    loop_nodes=TYPESCRIPT.loop_nodes,
    decorator_nodes=TYPESCRIPT.decorator_nodes,
)

JAVA = LanguageSpec(
    ts_name="java",
    import_nodes=frozenset({"import_declaration"}),
    class_nodes=frozenset({"class_declaration", "interface_declaration", "enum_declaration"}),
    function_nodes=frozenset({"method_declaration", "constructor_declaration"}),
    call_nodes=frozenset({"method_invocation", "object_creation_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "enhanced_for_statement", "while_statement",
         "switch_label", "catch_clause", "ternary_expression"}
    ),
    loop_nodes=frozenset({"for_statement", "enhanced_for_statement", "while_statement"}),
    decorator_nodes=frozenset({"annotation", "marker_annotation"}),
)

GO = LanguageSpec(
    ts_name="go",
    import_nodes=frozenset({"import_declaration"}),
    class_nodes=frozenset({"type_declaration"}),  # structs/interfaces
    function_nodes=frozenset({"function_declaration", "method_declaration"}),
    call_nodes=frozenset({"call_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "expression_case", "type_case", "select_statement"}
    ),
    loop_nodes=frozenset({"for_statement"}),
)

RUST = LanguageSpec(
    ts_name="rust",
    import_nodes=frozenset({"use_declaration"}),
    class_nodes=frozenset({"struct_item", "enum_item", "trait_item", "impl_item"}),
    function_nodes=frozenset({"function_item"}),
    call_nodes=frozenset({"call_expression", "macro_invocation"}),
    branch_nodes=frozenset(
        {"if_expression", "for_expression", "while_expression", "match_arm"}
    ),
    loop_nodes=frozenset({"for_expression", "while_expression", "loop_expression"}),
)

PHP = LanguageSpec(
    ts_name="php",
    import_nodes=frozenset({"namespace_use_declaration"}),
    class_nodes=frozenset({"class_declaration", "interface_declaration"}),
    function_nodes=frozenset({"function_definition", "method_declaration"}),
    call_nodes=frozenset({"function_call_expression", "member_call_expression", "scoped_call_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "foreach_statement", "while_statement",
         "switch_statement", "catch_clause", "conditional_expression"}
    ),
    loop_nodes=frozenset({"for_statement", "foreach_statement", "while_statement"}),
    decorator_nodes=frozenset({"attribute_group"}),
)

CSHARP = LanguageSpec(
    ts_name="csharp",
    import_nodes=frozenset({"using_directive"}),
    class_nodes=frozenset({"class_declaration", "interface_declaration", "record_declaration"}),
    function_nodes=frozenset({"method_declaration", "constructor_declaration"}),
    call_nodes=frozenset({"invocation_expression", "object_creation_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "foreach_statement", "while_statement",
         "switch_section", "catch_clause", "conditional_expression"}
    ),
    loop_nodes=frozenset({"for_statement", "foreach_statement", "while_statement"}),
    decorator_nodes=frozenset({"attribute_list"}),
)

CPP = LanguageSpec(
    ts_name="cpp",
    import_nodes=frozenset({"preproc_include"}),
    class_nodes=frozenset({"class_specifier", "struct_specifier"}),
    function_nodes=frozenset({"function_definition"}),
    call_nodes=frozenset({"call_expression"}),
    branch_nodes=frozenset(
        {"if_statement", "for_statement", "while_statement", "case_statement", "catch_clause",
         "conditional_expression"}
    ),
    loop_nodes=frozenset({"for_statement", "while_statement"}),
)

C = LanguageSpec(
    ts_name="c",
    import_nodes=frozenset({"preproc_include"}),
    class_nodes=frozenset({"struct_specifier"}),
    function_nodes=frozenset({"function_definition"}),
    call_nodes=frozenset({"call_expression"}),
    branch_nodes=frozenset({"if_statement", "for_statement", "while_statement", "case_statement"}),
    loop_nodes=frozenset({"for_statement", "while_statement"}),
)

# Language names here match app.parser.languages.Language values.
LANGUAGE_SPECS: dict[str, LanguageSpec] = {
    "python": PYTHON,
    "javascript": JAVASCRIPT,
    "typescript": TYPESCRIPT,
    "tsx": TSX,
    "java": JAVA,
    "go": GO,
    "rust": RUST,
    "php": PHP,
    "csharp": CSHARP,
    "cpp": CPP,
    "c": C,
}
