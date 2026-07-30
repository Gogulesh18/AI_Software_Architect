from app.analyzer.solid import analyze_solid
from app.graph.builder import build_graph
from app.parser.extractor import parse_source


def _analyze(src, path="a.py", lang="python"):
    pf = parse_source(path, lang, src)
    graph = build_graph([pf])
    return analyze_solid([pf], graph)


def test_srp_violation_from_many_methods():
    methods = "\n".join(f"    def m{i}(self):\n        pass\n" for i in range(20))
    src = f"class Big:\n{methods}\n"
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "SRP" in principles


def test_ocp_violation_from_type_switch():
    src = """
def handle(shape):
    if shape.type == "circle":
        pass
    elif shape.type == "square":
        pass
    elif shape.type == "triangle":
        pass
"""
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "OCP" in principles


def test_lsp_violation_from_stubbed_override():
    src = """
class Bird:
    def fly(self):
        return "flying"

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError
"""
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "LSP" in principles


def test_lsp_no_violation_for_real_override():
    src = """
class Bird:
    def fly(self):
        return "flying"

class Sparrow(Bird):
    def fly(self):
        return "flying fast"
"""
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "LSP" not in principles


def test_isp_violation_from_fat_interface():
    methods = "\n".join(f"    def m{i}(self):\n        pass\n" for i in range(10))
    src = f"class IRepository:\n{methods}\n"
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "ISP" in principles


def test_dip_violation_from_direct_construction():
    src = """
class EmailService:
    pass

class UserService:
    def register(self, user):
        service = EmailService()
        service.send(user)
"""
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "DIP" in principles


def test_dip_no_violation_for_constructor_composition():
    src = """
class EmailService:
    pass

class UserService:
    def __init__(self):
        self.service = EmailService()
"""
    result = _analyze(src)
    principles = {v["principle"] for v in result["violations"]}
    assert "DIP" not in principles


def test_clean_code_has_no_violations():
    src = "def add(a, b):\n    return a + b\n"
    result = _analyze(src)
    assert result["violations"] == []
