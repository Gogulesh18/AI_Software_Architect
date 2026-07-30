from app.graph.builder import build_graph, symbol_id
from app.parser.extractor import parse_source


def test_file_and_symbol_nodes_created():
    pf = parse_source("app/service.py", "python", "class Foo:\n    def bar(self):\n        pass\n")
    graph = build_graph([pf])

    assert graph.nodes["app/service.py"]["type"] == "file"
    cls_id = symbol_id("app/service.py", "Foo")
    assert graph.nodes[cls_id]["type"] == "class"
    method_id = symbol_id("app/service.py", "bar", "Foo")
    assert graph.nodes[method_id]["type"] == "method"
    assert graph.has_edge("app/service.py", cls_id)
    assert graph.has_edge(cls_id, method_id)


def test_relative_import_resolves_to_file_node():
    a = parse_source("src/a.ts", "typescript", "import { helper } from './b';\n")
    b = parse_source("src/b.ts", "typescript", "export function helper() {}\n")
    graph = build_graph([a, b])

    assert graph.has_edge("src/a.ts", "src/b.ts")
    edge_data = graph.get_edge_data("src/a.ts", "src/b.ts")
    assert any(d["type"] == "imports" for d in edge_data.values())


def test_unresolved_import_becomes_external_package_node():
    a = parse_source("src/a.ts", "typescript", "import React from 'react';\n")
    graph = build_graph([a])

    assert graph.has_node("external::react")
    assert graph.nodes["external::react"]["type"] == "external_package"
    assert graph.has_edge("src/a.ts", "external::react")


def test_inheritance_edge_resolved_when_unambiguous():
    base = parse_source("base.py", "python", "class Animal:\n    pass\n")
    child = parse_source("dog.py", "python", "class Dog(Animal):\n    pass\n")
    graph = build_graph([base, child])

    dog_id = symbol_id("dog.py", "Dog")
    animal_id = symbol_id("base.py", "Animal")
    assert graph.has_edge(dog_id, animal_id)
    edge_data = graph.get_edge_data(dog_id, animal_id)
    assert any(d["type"] == "inherits" for d in edge_data.values())


def test_ambiguous_inheritance_is_not_guessed():
    base1 = parse_source("a/base.py", "python", "class Animal:\n    pass\n")
    base2 = parse_source("b/base.py", "python", "class Animal:\n    pass\n")
    child = parse_source("dog.py", "python", "class Dog(Animal):\n    pass\n")
    graph = build_graph([base1, base2, child])

    dog_id = symbol_id("dog.py", "Dog")
    assert graph.out_degree(dog_id) == 0


def test_resolved_call_edge():
    pf = parse_source(
        "svc.py",
        "python",
        "class UserService:\n    def find(self):\n        return validate()\n\n\ndef validate():\n    return True\n",
    )
    graph = build_graph([pf])

    find_id = symbol_id("svc.py", "find", "UserService")
    validate_id = symbol_id("svc.py", "validate")
    assert graph.has_edge(find_id, validate_id)
