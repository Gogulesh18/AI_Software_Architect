from app.analyzer.architecture import detect_architecture
from app.graph.summary import compute_summary
from app.parser.ecosystem import EcosystemInfo
from app.parser.extractor import parse_source


def _pf(path):
    return parse_source(path, "python", "x = 1\n")


def test_mvc_detected_from_django_style_app():
    files = [_pf("app/models.py"), _pf("app/views.py"), _pf("app/urls.py")]
    summary = compute_summary(files, EcosystemInfo([], []))

    result = detect_architecture(files, summary)

    assert result["primary_style"] == "MVC"
    assert result["confidence"] > 0
    assert result["evidence"]


def test_layered_detected_from_controller_service_repository():
    files = [
        _pf("src/controllers/user_controller.py"),
        _pf("src/services/user_service.py"),
        _pf("src/repositories/user_repository.py"),
    ]
    summary = compute_summary(files, EcosystemInfo([], []))

    result = detect_architecture(files, summary)

    assert result["primary_style"] in ("Layered", "Clean Architecture")


def test_monolith_default_when_no_signals():
    files = [_pf("main.py"), _pf("utils.py")]
    summary = compute_summary(files, EcosystemInfo([], []))

    result = detect_architecture(files, summary)

    assert result["primary_style"] == "Monolith"


def test_all_candidates_present_and_sorted_desc():
    files = [_pf("main.py")]
    summary = compute_summary(files, EcosystemInfo([], []))

    result = detect_architecture(files, summary)

    confidences = [c["confidence"] for c in result["all_candidates"]]
    assert confidences == sorted(confidences, reverse=True)
