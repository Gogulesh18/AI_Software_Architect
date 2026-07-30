"""SOLID principle violation heuristics, each with a file:line reference and reasoning.

Real static verification of SOLID would need a type system; these are the
same textbook smells a reviewer looks for: a class doing too much (SRP), a
type-switch that should be polymorphism (OCP), a subclass that narrows a
contract instead of fulfilling it (LSP), a fat interface (ISP), and
concrete-class construction instead of injection (DIP).
"""

import re
from typing import Any

import networkx as nx

from app.parser.models import ParsedFile

SRP_METHOD_THRESHOLD = 15
SRP_LOC_THRESHOLD = 300
ISP_METHOD_THRESHOLD = 7
_TYPE_SWITCH_RE = re.compile(r"\.(type|kind|status|category)\s*==")
_INTERFACE_NAME_RE = re.compile(r"^I[A-Z]")
_STUB_BODY_RE = re.compile(r"^\s*(raise\s+NotImplementedError|throw\s+new\s+\w*Error|pass|NotImplementedException)")


def analyze_solid(parsed_files: list[ParsedFile], graph: nx.MultiDiGraph) -> dict:
    violations: list[dict] = []

    all_class_names = {cls.name for pf in parsed_files for cls in pf.classes}

    for pf in parsed_files:
        for cls in pf.classes:
            methods = [m for m in pf.functions if m.parent_class == cls.name]
            violations.extend(_srp(pf, cls, methods))
            violations.extend(_isp(pf, cls, methods))
            violations.extend(_dip(pf, cls, methods, all_class_names))

        for func in pf.functions:
            violations.extend(_ocp(pf, func))

        violations.extend(_lsp(pf))

    by_principle: dict[str, int] = {}
    for v in violations:
        by_principle[v["principle"]] = by_principle.get(v["principle"], 0) + 1

    return {"summary": by_principle, "violations": violations}


def _srp(pf: ParsedFile, cls, methods) -> list[dict]:
    loc = cls.end_line - cls.start_line + 1
    if len(methods) > SRP_METHOD_THRESHOLD or loc > SRP_LOC_THRESHOLD:
        return [
            {
                "principle": "SRP",
                "file": pf.relative_path,
                "symbol": cls.name,
                "line": cls.start_line,
                "message": f"'{cls.name}' has {len(methods)} methods across {loc} lines — likely handling more than one responsibility",
            }
        ]
    return []


def _ocp(pf: ParsedFile, func) -> list[dict]:
    body_lines = pf.source.splitlines()[func.start_line - 1 : func.end_line]
    matches = sum(1 for line in body_lines if _TYPE_SWITCH_RE.search(line))
    if matches >= 3:
        return [
            {
                "principle": "OCP",
                "file": pf.relative_path,
                "symbol": func.name,
                "line": func.start_line,
                "message": f"'{func.name}' branches {matches} times on a type/kind/status field — adding a new case means editing this function; consider polymorphism instead",
            }
        ]
    return []


def _lsp(pf: ParsedFile) -> list[dict]:
    violations = []
    # Heterogeneous per-class scratch structure (base_classes: list[str],
    # methods: dict[str, ParsedSymbol]) — typed loosely rather than a small
    # dataclass, since it never leaves this function.
    methods_by_class: dict[str, dict[str, Any]] = {}
    for cls in pf.classes:
        methods_by_class.setdefault(cls.name, {"base_classes": cls.base_classes, "methods": {}})
    for func in pf.functions:
        if func.parent_class and func.parent_class in methods_by_class:
            methods_by_class[func.parent_class]["methods"][func.name] = func

    for cls_name, info in methods_by_class.items():
        bases = [b.rsplit(".", 1)[-1] for b in info["base_classes"]]
        if not bases:
            continue
        for method_name, func in info["methods"].items():
            if not any(method_name in methods_by_class.get(base, {}).get("methods", {}) for base in bases):
                continue  # not actually an override we can see in this file
            body_lines = pf.source.splitlines()[func.start_line - 1 : func.end_line]
            non_blank = [ln for ln in body_lines[1:] if ln.strip()]  # skip the def line
            if non_blank and all(_STUB_BODY_RE.match(ln) for ln in non_blank):
                violations.append(
                    {
                        "principle": "LSP",
                        "file": pf.relative_path,
                        "symbol": f"{cls_name}.{method_name}",
                        "line": func.start_line,
                        "message": f"'{cls_name}.{method_name}' overrides a base-class method but only raises/stubs — callers substituting '{cls_name}' for its base will break",
                    }
                )
    return violations


def _isp(pf: ParsedFile, cls, methods) -> list[dict]:
    if _INTERFACE_NAME_RE.match(cls.name) and len(methods) > ISP_METHOD_THRESHOLD:
        return [
            {
                "principle": "ISP",
                "file": pf.relative_path,
                "symbol": cls.name,
                "line": cls.start_line,
                "message": f"interface '{cls.name}' declares {len(methods)} methods — implementers are forced to depend on methods they may not use",
            }
        ]
    return []


def _dip(pf: ParsedFile, cls, methods, all_class_names: set[str]) -> list[dict]:
    violations = []
    for method in methods:
        if method.name in ("__init__", "constructor", cls.name):
            continue  # construction inside the constructor's own composition root is normal
        constructed = [call for call in method.calls if call.rsplit(".", 1)[-1] in all_class_names]
        for target in constructed:
            violations.append(
                {
                    "principle": "DIP",
                    "file": pf.relative_path,
                    "symbol": f"{cls.name}.{method.name}",
                    "line": method.start_line,
                    "message": f"'{cls.name}.{method.name}' directly constructs '{target}' instead of receiving it as a dependency",
                }
            )
            break  # one example per method is enough signal
    return violations
