"""Security checks: hardcoded secrets, injection, unsafe deserialization, weak auth, missing validation."""

from app.analyzer.security.detector import analyze_security

__all__ = ["analyze_security"]
