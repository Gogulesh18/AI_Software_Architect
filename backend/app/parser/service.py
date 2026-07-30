"""Top-level parsing orchestration: FileRecord list -> ParsedFile list."""

import logging

from app.ingest.files import FileRecord, read_text_safe
from app.parser.extractor import parse_source
from app.parser.languages import DEEP_PARSE_LANGUAGES, detect_language
from app.parser.models import ParsedFile

logger = logging.getLogger(__name__)


def parse_files(records: list[FileRecord]) -> list[ParsedFile]:
    parsed: list[ParsedFile] = []

    for record in records:
        language = detect_language(record.relative_path)
        content = read_text_safe(record.absolute_path)
        if content is None:
            continue

        if language in DEEP_PARSE_LANGUAGES:
            try:
                parsed.append(parse_source(record.relative_path, language, content))
                continue
            except Exception as exc:  # noqa: BLE001 - pragma: no cover - defensive
                logger.warning("Falling back to shallow parse for %s: %s", record.relative_path, exc)

        parsed.append(
            ParsedFile(
                relative_path=record.relative_path,
                language=language,
                loc=len(content.splitlines()),
                source=content,
            )
        )

    return parsed
