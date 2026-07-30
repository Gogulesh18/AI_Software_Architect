"""ORM/database model detection -> tables, columns, PK/FK, for the ER diagram.

Heuristic and regex-based, not a real per-ORM schema compiler: reliable
enough to draw a useful ER diagram for the common declarative styles of
each named ORM (SQLAlchemy, Django ORM, TypeORM, Hibernate/JPA, Entity
Framework, Mongoose, Prisma), not guaranteed field-perfect on every variant.
"""

import re
from dataclasses import dataclass, field

from app.parser.models import ParsedFile

_ID_LIKE = {"id", "pk", "uuid"}


@dataclass(slots=True)
class Column:
    name: str
    type: str
    primary_key: bool = False
    foreign_key: str | None = None


@dataclass(slots=True)
class Table:
    name: str
    orm: str
    file: str
    columns: list[Column] = field(default_factory=list)


def detect_database(parsed_files: list[ParsedFile]) -> dict:
    tables: list[Table] = []

    for pf in parsed_files:
        if pf.language == "python":
            tables += _sqlalchemy_models(pf)
            tables += _django_models(pf)
        elif pf.language in ("typescript", "tsx", "javascript"):
            tables += _typeorm_entities(pf)
            tables += _mongoose_schemas(pf)
        elif pf.language == "java":
            tables += _jpa_entities(pf)
        elif pf.language == "csharp":
            tables += _ef_entities(pf)
        elif pf.relative_path.endswith(".prisma"):
            tables += _prisma_models(pf)

    relationships = _infer_relationships(tables)

    return {
        "orms_detected": sorted({t.orm for t in tables}),
        "tables": [
            {
                "name": t.name,
                "orm": t.orm,
                "file": t.file,
                "columns": [
                    {"name": c.name, "type": c.type, "primary_key": c.primary_key, "foreign_key": c.foreign_key}
                    for c in t.columns
                ],
            }
            for t in tables
        ],
        "relationships": relationships,
    }


def _class_body(pf: ParsedFile, start_line: int, end_line: int) -> str:
    lines = pf.source.splitlines()
    return "\n".join(lines[start_line - 1 : end_line])


def _sqlalchemy_models(pf: ParsedFile) -> list[Table]:
    tables = []
    col_re = re.compile(r"^\s*(\w+)\s*(?::\s*Mapped\[[^\]]*\])?\s*=\s*(?:db\.)?(?:mapped_column|Column)\((.*)\)\s*$")
    for cls in pf.classes:
        body = _class_body(pf, cls.start_line, cls.end_line)
        if "__tablename__" not in body:
            continue
        table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', body)
        table_name = table_match.group(1) if table_match else cls.name
        columns = []
        for line in body.splitlines():
            m = col_re.match(line)
            if not m:
                continue
            name, args = m.group(1), m.group(2)
            type_match = re.match(r"\s*([A-Za-z_][\w.]*)", args)
            fk_match = re.search(r"ForeignKey\(\s*[\"']([^\"']+)[\"']", args)
            columns.append(
                Column(
                    name=name,
                    type=type_match.group(1) if type_match else "unknown",
                    primary_key="primary_key=True" in args or name.lower() in _ID_LIKE,
                    foreign_key=fk_match.group(1) if fk_match else None,
                )
            )
        tables.append(Table(name=table_name, orm="sqlalchemy", file=pf.relative_path, columns=columns))
    return tables


def _django_models(pf: ParsedFile) -> list[Table]:
    tables = []
    field_re = re.compile(r"^\s*(\w+)\s*=\s*models\.(\w+)\((.*)\)\s*$")
    for cls in pf.classes:
        if "Model" not in cls.base_classes:
            continue
        body = _class_body(pf, cls.start_line, cls.end_line)
        columns = []
        for line in body.splitlines():
            m = field_re.match(line)
            if not m:
                continue
            name, field_type, args = m.group(1), m.group(2), m.group(3)
            fk_match = None
            if field_type in ("ForeignKey", "OneToOneField", "ManyToManyField"):
                target = re.match(r"\s*[\"']?(\w+)[\"']?", args)
                fk_match = target.group(1) if target else None
            columns.append(
                Column(
                    name=name,
                    type=field_type,
                    primary_key=field_type == "AutoField" or "primary_key=True" in args,
                    foreign_key=fk_match,
                )
            )
        # Always emit a table: the class matched the Model base even if it has
        # zero explicit fields (Django gives every model an implicit `id`).
        columns.insert(0, Column(name="id", type="AutoField", primary_key=True))
        tables.append(Table(name=cls.name, orm="django", file=pf.relative_path, columns=columns))
    return tables


_DECORATED_FIELD_PATTERNS = {
    # language -> (decorator_line_re, field_line_re, (name_group, type_group))
    "ts": (re.compile(r"^\s*@(\w+)\("), re.compile(r"^\s*(?:\w+\s+)*(\w+)\s*[?!]?\s*:\s*([\w<>\[\].]+)"), (1, 2)),
    "java": (re.compile(r"^\s*@(\w+)"), re.compile(r"^\s*(?:private|public|protected)\s+([\w<>\[\],.\s]+?)\s+(\w+)\s*;"), (2, 1)),
    "csharp": (re.compile(r"^\s*\[(\w+)"), re.compile(r"^\s*(?:public|private|protected)\s+(?:virtual\s+)?([\w<>\[\],.]+)\s+(\w+)\s*\{"), (2, 1)),
}


def _scan_decorated_fields(body: str, lang: str) -> list[tuple[str, str, list[str]]]:
    deco_re, field_re, (name_idx, type_idx) = _DECORATED_FIELD_PATTERNS[lang]
    pending: list[str] = []
    results: list[tuple[str, str, list[str]]] = []
    for line in body.splitlines():
        deco_match = deco_re.match(line)
        if deco_match:
            pending.append(deco_match.group(1))
            continue
        field_match = field_re.match(line)
        if field_match and pending:
            results.append((field_match.group(name_idx), field_match.group(type_idx), pending))
            pending = []
        elif field_match or line.strip() and not line.strip().startswith(("//", "*", "/*")):
            pending = []
    return results


def _typeorm_entities(pf: ParsedFile) -> list[Table]:
    tables = []
    for cls in pf.classes:
        if not any("Entity" in d for d in cls.decorators):
            continue
        body = _class_body(pf, cls.start_line, cls.end_line)
        columns = []
        for name, type_str, decorators in _scan_decorated_fields(body, "ts"):
            is_pk = any(d in ("PrimaryGeneratedColumn", "PrimaryColumn") for d in decorators)
            is_relation = any(d in ("ManyToOne", "OneToOne", "ManyToMany") for d in decorators)
            columns.append(
                Column(name=name, type=type_str, primary_key=is_pk, foreign_key=type_str if is_relation else None)
            )
        tables.append(Table(name=cls.name, orm="typeorm", file=pf.relative_path, columns=columns))
    return tables


def _jpa_entities(pf: ParsedFile) -> list[Table]:
    tables = []
    for cls in pf.classes:
        if not any("Entity" in d for d in cls.decorators):
            continue
        body = _class_body(pf, cls.start_line, cls.end_line)
        columns = []
        for name, type_str, decorators in _scan_decorated_fields(body, "java"):
            is_pk = "Id" in decorators
            is_relation = any(d in ("ManyToOne", "OneToOne", "ManyToMany") for d in decorators)
            columns.append(
                Column(name=name, type=type_str, primary_key=is_pk, foreign_key=type_str if is_relation else None)
            )
        tables.append(Table(name=cls.name, orm="hibernate/jpa", file=pf.relative_path, columns=columns))
    return tables


def _ef_entities(pf: ParsedFile) -> list[Table]:
    # EF Core POCOs are often convention-based (no attributes at all), so the
    # reliable signal is a `DbSet<EntityName>` property somewhere in a
    # DbContext, not annotations on the entity class itself.
    entity_names: set[str] = set()
    for pf2 in [pf]:
        entity_names |= set(re.findall(r"DbSet<(\w+)>", pf2.source))

    tables = []
    for cls in pf.classes:
        if cls.name not in entity_names:
            continue
        body = _class_body(pf, cls.start_line, cls.end_line)
        columns = []
        for name, type_str, decorators in _scan_decorated_fields(body, "csharp"):
            is_pk = "Key" in decorators or name.lower() in _ID_LIKE
            is_relation = "ForeignKey" in decorators
            columns.append(
                Column(name=name, type=type_str, primary_key=is_pk, foreign_key=type_str if is_relation else None)
            )
        tables.append(Table(name=cls.name, orm="entity framework", file=pf.relative_path, columns=columns))
    return tables


def _mongoose_schemas(pf: ParsedFile) -> list[Table]:
    tables = []
    for match in re.finditer(r"(\w+)\s*=\s*new\s+(?:mongoose\.)?Schema\(\s*\{", pf.source):
        name = match.group(1).removesuffix("Schema") or match.group(1)
        # Grab the object literal body with a simple brace counter (regex
        # can't reliably match nested braces).
        start = match.end() - 1
        body = _balanced_braces(pf.source, start)
        columns = []
        for field_match in re.finditer(r"(\w+)\s*:\s*\{", body):
            columns.append(Column(name=field_match.group(1), type="mixed"))
        if not columns:
            for field_match in re.finditer(r"(\w+)\s*:\s*(String|Number|Boolean|Date|ObjectId)\b", body):
                columns.append(Column(name=field_match.group(1), type=field_match.group(2)))
        tables.append(Table(name=name, orm="mongoose", file=pf.relative_path, columns=columns))
    return tables


def _balanced_braces(text: str, open_brace_index: int) -> str:
    depth = 0
    for i in range(open_brace_index, min(len(text), open_brace_index + 20000)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace_index : i + 1]
    return text[open_brace_index : open_brace_index + 2000]


def _prisma_models(pf: ParsedFile) -> list[Table]:
    tables = []
    for model_match in re.finditer(r"model\s+(\w+)\s*\{([^}]*)\}", pf.source, re.DOTALL):
        name, body = model_match.group(1), model_match.group(2)
        columns = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith(("//", "@@")):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            field_name, field_type = parts[0], parts[1]
            columns.append(
                Column(
                    name=field_name,
                    type=field_type,
                    primary_key="@id" in line,
                    foreign_key=field_type if "@relation" in line else None,
                )
            )
        tables.append(Table(name=name, orm="prisma", file=pf.relative_path, columns=columns))
    return tables


def _infer_relationships(tables: list[Table]) -> list[dict]:
    by_name = {t.name.lower(): t.name for t in tables}
    relationships = []
    for t in tables:
        for c in t.columns:
            if not c.foreign_key:
                continue
            target_key = re.sub(r"\[\]|Array<|>|<.*>", "", c.foreign_key).strip().lower()
            target = by_name.get(target_key) or by_name.get(target_key.rstrip("s"))
            if target and target != t.name:
                relationships.append({"from": t.name, "to": target, "via": c.name})
    return relationships
