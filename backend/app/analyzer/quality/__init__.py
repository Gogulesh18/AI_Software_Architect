"""Code quality checks: complexity, long methods, dead/duplicate code, god classes, code smells."""

from app.analyzer.quality.detector import analyze_quality

__all__ = ["analyze_quality"]
