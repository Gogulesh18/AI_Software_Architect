"""Design pattern detection: name-convention + method-signature heuristics.

This is not semantic pattern recognition (that would need real type/data-flow
analysis) — it's the same thing an experienced reviewer does at a glance:
"a class named XyzFactory with create-ish methods is almost certainly a
Factory". Every match carries a `reason` string explaining exactly which
signal triggered it, per the product brief's requirement to explain *why*.
MVC and Clean Architecture are intentionally not duplicated here — those are
whole-repo architecture styles already covered by app.analyzer.architecture.
"""

import re

import networkx as nx

from app.parser.models import ParsedFile, ParsedSymbol

_CRUD_METHODS = {"find", "findbyid", "findall", "get", "getbyid", "getall", "save", "create", "update", "delete", "remove"}
_OBSERVER_METHODS = {"subscribe", "unsubscribe", "notify", "emit", "on", "addlistener", "addeventlistener", "dispatch", "publish"}
_DI_MARKERS = ("Depends(", "@Autowired", "@Inject", "@Injectable", "@inject")


def detect_patterns(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph) -> dict:
    matches: list[dict] = []

    subclass_counts = _subclass_counts(parsed_files)

    for pf in parsed_files:
        for cls in pf.classes:
            method_names = {m.name.lower() for m in pf.functions if m.parent_class == cls.name}
            matches.extend(_class_pattern_matches(pf, cls, method_names, subclass_counts))

        for func in pf.functions:
            matches.extend(_function_pattern_matches(pf, func))

        if any(marker in pf.source for marker in _DI_MARKERS):
            matches.append(
                {
                    "pattern": "Dependency Injection",
                    "file": pf.relative_path,
                    "symbol": None,
                    "line": 0,
                    "reason": "dependency-injection framework marker found (Depends/@Autowired/@Inject/@Injectable)",
                }
            )

    matches.extend(_cqrs_matches(parsed_files))

    by_pattern: dict[str, int] = {}
    for m in matches:
        by_pattern[m["pattern"]] = by_pattern.get(m["pattern"], 0) + 1

    return {"summary": by_pattern, "matches": matches}


def _subclass_counts(parsed_files: list[ParsedFile]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pf in parsed_files:
        for cls in pf.classes:
            for base in cls.base_classes:
                short = base.rsplit(".", 1)[-1]
                counts[short] = counts.get(short, 0) + 1
    return counts


def _class_pattern_matches(pf: ParsedFile, cls: ParsedSymbol, method_names: set[str], subclass_counts: dict[str, int]) -> list[dict]:
    matches = []
    name = cls.name
    body = "\n".join(pf.source.splitlines()[cls.start_line - 1 : cls.end_line])

    def add(pattern: str, reason: str) -> None:
        matches.append({"pattern": pattern, "file": pf.relative_path, "symbol": name, "line": cls.start_line, "reason": reason})

    if re.search(r"Factory$", name):
        add("Factory", f"class name '{name}' follows the *Factory naming convention")

    if re.search(r"Builder$", name) and "build" in method_names:
        add("Builder", f"class name '{name}' ends in Builder and defines a build() method")

    if re.search(r"(Repository|Repo)$", name) and len(method_names & _CRUD_METHODS) >= 2:
        add("Repository", f"class name '{name}' ends in Repository/Repo and exposes CRUD-style methods ({', '.join(sorted(method_names & _CRUD_METHODS))})")

    if "_instance" in body and re.search(r"\b(instance|getInstance|get_instance)\b", body):
        add("Singleton", f"class '{name}' holds a private instance reference with an instance accessor")

    if re.search(r"Strategy$", name):
        add("Strategy", f"class name '{name}' follows the *Strategy naming convention")
    elif subclass_counts.get(name, 0) >= 2:
        add("Strategy", f"'{name}' has {subclass_counts[name]} distinct subclasses — likely an interchangeable-implementation (Strategy) role")

    if re.search(r"(Adapter|Wrapper)$", name):
        add("Adapter", f"class name '{name}' follows the *Adapter/*Wrapper naming convention")

    if re.search(r"Facade$", name):
        add("Facade", f"class name '{name}' follows the *Facade naming convention")

    if re.search(r"(Observer|Listener|Subscriber)$", name) or len(method_names & _OBSERVER_METHODS) >= 2:
        matched_methods = method_names & _OBSERVER_METHODS
        reason = f"class name '{name}' follows the *Observer/*Listener convention" if re.search(r"(Observer|Listener|Subscriber)$", name) else f"'{name}' exposes pub/sub-style methods ({', '.join(sorted(matched_methods))})"
        add("Observer", reason)

    if re.search(r"Decorator$", name):
        add("Decorator", f"class name '{name}' follows the *Decorator naming convention")

    if re.search(r"Command$", name) and method_names & {"execute", "run", "handle"}:
        add("Command", f"class name '{name}' ends in Command and defines an execute/run/handle method")

    return matches


def _function_pattern_matches(pf: ParsedFile, func: ParsedSymbol) -> list[dict]:
    matches: list[dict] = []
    if func.kind != "function":
        return matches
    if re.match(r"(create_|make_|build_)", func.name.lower()) and func.complexity > 2:
        matches.append(
            {
                "pattern": "Factory",
                "file": pf.relative_path,
                "symbol": func.name,
                "line": func.start_line,
                "reason": f"function '{func.name}' has a create/make/build name and branches ({func.complexity} paths) to produce different results",
            }
        )
    return matches


def _cqrs_matches(parsed_files: list[ParsedFile]) -> list[dict]:
    command_classes = []
    query_classes = []
    handler_classes = []
    for pf in parsed_files:
        for cls in pf.classes:
            if re.search(r"Command$", cls.name):
                command_classes.append((pf.relative_path, cls.name, cls.start_line))
            elif re.search(r"Query$", cls.name):
                query_classes.append((pf.relative_path, cls.name, cls.start_line))
            elif re.search(r"Handler$", cls.name):
                handler_classes.append((pf.relative_path, cls.name, cls.start_line))

    if len(command_classes) + len(query_classes) >= 2 and len(handler_classes) >= 2:
        file, name, line = command_classes[0] if command_classes else query_classes[0]
        return [
            {
                "pattern": "CQRS",
                "file": file,
                "symbol": name,
                "line": line,
                "reason": f"repo defines {len(command_classes)} Command class(es), {len(query_classes)} Query class(es), and {len(handler_classes)} Handler class(es) — command/query separation with dedicated handlers",
            }
        ]
    return []
