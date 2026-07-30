"""Architecture style classification (monolith, microservices, MVC, etc.) with confidence scoring."""

from app.analyzer.architecture.detector import detect_architecture

__all__ = ["detect_architecture"]
