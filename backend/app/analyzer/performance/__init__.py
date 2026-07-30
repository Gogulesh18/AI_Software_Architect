"""Performance checks: N+1 queries, blocking calls, expensive loops, missing cache."""

from app.analyzer.performance.detector import analyze_performance

__all__ = ["analyze_performance"]
