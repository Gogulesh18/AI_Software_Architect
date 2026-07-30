from app.parser.extractor import parse_source


def test_python_base_classes():
    result = parse_source("a.py", "python", "class Foo(Bar, Baz):\n    pass\n")
    assert set(result.classes[0].base_classes) == {"Bar", "Baz"}


def test_typescript_extends_implements():
    result = parse_source("a.ts", "typescript", "class Foo extends Bar implements Baz {}\n")
    assert set(result.classes[0].base_classes) == {"Bar", "Baz"}


def test_java_extends_implements():
    result = parse_source("A.java", "java", "class Foo extends Bar implements Baz {}\n")
    assert set(result.classes[0].base_classes) == {"Bar", "Baz"}


def test_csharp_base_list():
    result = parse_source("A.cs", "csharp", "class Foo : Bar, IBaz {}\n")
    assert set(result.classes[0].base_classes) == {"Bar", "IBaz"}


def test_php_extends_implements():
    src = "<?php\nclass Foo extends Bar implements Baz {}\n"
    result = parse_source("A.php", "php", src)
    assert set(result.classes[0].base_classes) == {"Bar", "Baz"}


def test_cpp_base_class_clause():
    result = parse_source("a.cpp", "cpp", "class Foo : public Bar, public Baz {};\n")
    assert set(result.classes[0].base_classes) == {"Bar", "Baz"}


def test_no_base_classes_is_empty_list():
    result = parse_source("a.py", "python", "class Foo:\n    pass\n")
    assert result.classes[0].base_classes == []
