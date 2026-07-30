from app.analyzer.quality import analyze_quality
from app.graph.builder import build_graph
from app.parser.extractor import parse_source


def test_high_complexity_detected():
    lines = ["def f():"]
    for i in range(15):
        lines.append(f"    if x == {i}:")
        lines.append("        pass")
    src = "\n".join(lines) + "\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])

    result = analyze_quality([pf], graph)

    categories = {f["category"] for f in result["findings"]}
    assert "high_complexity" in categories
    assert result["metrics"]["max_complexity"] > 10


def test_long_method_detected():
    body = "\n".join(f"    x{i} = {i}" for i in range(60))
    src = f"def big():\n{body}\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])

    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "long_method" in categories


def test_deep_nesting_detected():
    src = """
def f():
    if a:
        if b:
            if c:
                if d:
                    if e:
                        pass
"""
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "deep_nesting" in categories


def test_god_class_detected():
    methods = "\n".join(f"    def m{i}(self):\n        pass\n" for i in range(25))
    padding = "\n".join(f"    # padding line {i}" for i in range(300))
    src = f"class Big:\n{methods}\n{padding}\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "god_class" in categories


def test_magic_number_detected():
    src = "def f():\n    return price * 47328\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "magic_number" in categories


def test_duplicate_code_detected():
    block = (
        "    total = 0\n"
        "    for item in items:\n"
        "        total += item.price\n"
        "        total += item.tax\n"
        "        total += item.shipping\n"
        "    return total"
    )
    src_a = f"def calc_a():\n{block}\n"
    src_b = f"def calc_b():\n{block}\n"
    pf_a = parse_source("a.py", "python", src_a)
    pf_b = parse_source("b.py", "python", src_b)
    graph = build_graph([pf_a, pf_b])

    result = analyze_quality([pf_a, pf_b], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "duplicate_code" in categories


def test_dead_code_flags_uncalled_function():
    src = "def unused():\n    pass\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "dead_code" in categories


def test_dead_code_ignores_called_function():
    src = "def used():\n    pass\n\ndef caller():\n    used()\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    dead_names = {f["symbol"] for f in result["findings"] if f["category"] == "dead_code"}
    assert "used" not in dead_names


def test_clean_code_has_minimal_findings():
    src = "def add(a, b):\n    return a + b\n"
    pf = parse_source("a.py", "python", src)
    graph = build_graph([pf])
    result = analyze_quality([pf], graph)
    categories = {f["category"] for f in result["findings"]}
    assert "high_complexity" not in categories
    assert "long_method" not in categories
