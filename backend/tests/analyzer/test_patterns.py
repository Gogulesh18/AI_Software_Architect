from app.analyzer.patterns import detect_patterns
from app.graph.builder import build_graph
from app.parser.extractor import parse_source


def _detect(src, path="a.py", lang="python"):
    pf = parse_source(path, lang, src)
    graph = build_graph([pf])
    return detect_patterns([pf], graph)


def test_factory_detected_by_class_name():
    result = _detect("class UserFactory:\n    def create(self):\n        pass\n")
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Factory" in patterns


def test_builder_requires_build_method():
    result = _detect("class ReportBuilder:\n    def build(self):\n        pass\n")
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Builder" in patterns


def test_builder_not_detected_without_build_method():
    result = _detect("class ReportBuilder:\n    def other(self):\n        pass\n")
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Builder" not in patterns


def test_repository_detected_from_crud_methods():
    src = "class UserRepository:\n    def find(self, id):\n        pass\n    def save(self, u):\n        pass\n"
    result = _detect(src)
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Repository" in patterns


def test_singleton_detected():
    src = """
class Config:
    _instance = None

    @staticmethod
    def get_instance():
        return Config._instance
"""
    result = _detect(src)
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Singleton" in patterns


def test_observer_detected_from_methods():
    src = "class EventBus:\n    def subscribe(self, cb):\n        pass\n    def notify(self, e):\n        pass\n"
    result = _detect(src)
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Observer" in patterns


def test_dependency_injection_detected_from_fastapi_depends():
    src = "def endpoint(db: Session = Depends(get_db)):\n    pass\n"
    result = _detect(src)
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Dependency Injection" in patterns


def test_command_pattern_detected():
    src = "class CreateOrderCommand:\n    def execute(self):\n        pass\n"
    result = _detect(src)
    patterns = {m["pattern"] for m in result["matches"]}
    assert "Command" in patterns


def test_reason_is_always_present():
    result = _detect("class UserFactory:\n    def create(self):\n        pass\n")
    for m in result["matches"]:
        assert m["reason"]


def test_no_patterns_in_plain_code():
    result = _detect("def add(a, b):\n    return a + b\n")
    assert result["matches"] == []
