"""REST/GraphQL/gRPC/WebSocket endpoint detection + auth signal detection.

Regex-over-source, not AST-driven: route registration syntax (decorator
args, `app.get("/x", ...)` call args) needs the literal string argument,
which is cheaper to get with a targeted regex per framework than by walking
call-expression argument nodes for every language again. Line numbers are
derived from the match offset.
"""

import re

from app.parser.models import ParsedFile

# (framework, method_group_or_fixed, compiled_pattern, path_group)
# "method" is either a regex group index or a literal string when the
# pattern only ever means one HTTP method (or is method-agnostic).
_ROUTE_PATTERNS: list[tuple[str, str | int, re.Pattern, int | None]] = [
    ("fastapi/flask", 1, re.compile(r'@(?:app|router|\w+)\.(get|post|put|delete|patch|options|head)\(\s*["\']([^"\']+)["\']'), 2),
    ("fastapi", "WEBSOCKET", re.compile(r'@(?:app|router)\.websocket\(\s*["\']([^"\']+)["\']'), 1),
    ("flask", "ANY", re.compile(r'@\w+\.route\(\s*["\']([^"\']+)["\']'), 1),
    # negative lookbehind excludes `@app.get(...)` decorator syntax, already
    # matched by the fastapi/flask pattern above — without it, every FastAPI
    # decorator route was double-counted as an Express call too.
    ("express", 1, re.compile(r'(?<!@)\b(?:app|router)\.(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'), 2),
    ("nestjs", 1, re.compile(r'@(Get|Post|Put|Delete|Patch)\(\s*["\']?([^"\')]*)["\']?\s*\)'), 2),
    ("spring", 1, re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'), 2),
    ("spring", "ANY", re.compile(r'@RequestMapping\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']'), 1),
    ("laravel", 1, re.compile(r'Route::(get|post|put|delete|patch)\(\s*["\']([^"\']+)["\']'), 2),
    ("aspnet", 1, re.compile(r'\[Http(Get|Post|Put|Delete|Patch)(?:\(\s*["\']([^"\']*)["\']\s*)?\]'), 2),
]

_GRAPHQL_IMPORT_HINTS = {"graphql", "apollo-server", "strawberry", "graphene", "@nestjs/graphql", "ariadne"}
_GRPC_IMPORT_HINTS = {"grpc", "@grpc/grpc-js", "google.golang.org/grpc", "grpcio"}
_WEBSOCKET_IMPORT_HINTS = {"socket.io", "ws", "@nestjs/websockets", "websockets", "channels"}
_AUTH_HINTS = {
    "jwt", "pyjwt", "jsonwebtoken", "passport", "passport-jwt", "oauthlib", "authlib",
    "django.contrib.auth", "flask_login", "flask-login", "spring-security",
}
_AUTH_CODE_MARKERS = ("@UseGuards", "[Authorize]", "HTTPBearer", "OAuth2PasswordBearer", "@login_required", "@jwt_required")


def detect_api_surface(parsed_files: list[ParsedFile]) -> dict:
    endpoints: list[dict] = []
    protocols: set[str] = set()
    all_imports = {raw.lower() for pf in parsed_files for raw in pf.imports}

    for pf in parsed_files:
        for framework, method, pattern, path_group in _ROUTE_PATTERNS:
            for m in pattern.finditer(pf.source):
                method_name = method if isinstance(method, str) else (m.group(method).upper() or "GET")
                path = m.group(path_group).strip() if path_group else ""
                line = pf.source.count("\n", 0, m.start()) + 1
                endpoints.append(
                    {"method": method_name, "path": path or "(dynamic)", "file": pf.relative_path, "line": line, "framework": framework}
                )
                protocols.add("WebSocket" if method_name == "WEBSOCKET" else "REST")

        if pf.relative_path.endswith((".graphql", ".gql")):
            protocols.add("GraphQL")
        if any(sym.name in ("Query", "Mutation", "Resolver") for sym in pf.classes):
            protocols.add("GraphQL")
        if any("@Resolver" in d or "@Query" in d or "@Mutation" in d for sym in pf.symbols for d in sym.decorators):
            protocols.add("GraphQL")
        if pf.relative_path.endswith(".proto"):
            protocols.add("gRPC")

    if all_imports & _GRAPHQL_IMPORT_HINTS:
        protocols.add("GraphQL")
    if all_imports & _GRPC_IMPORT_HINTS:
        protocols.add("gRPC")
    if all_imports & _WEBSOCKET_IMPORT_HINTS:
        protocols.add("WebSocket")

    auth = _detect_auth(parsed_files, all_imports)

    return {
        "protocols": sorted(protocols),
        "endpoints": endpoints,
        "endpoint_count": len(endpoints),
        "auth": auth,
    }


def _detect_auth(parsed_files: list[ParsedFile], all_imports: set[str]) -> dict:
    mechanisms: set[str] = set()

    if all_imports & {"jwt", "pyjwt", "jsonwebtoken"}:
        mechanisms.add("JWT")
    if all_imports & {"passport", "passport-jwt"}:
        mechanisms.add("Passport.js")
    if all_imports & {"oauthlib", "authlib"} or any("oauth" in i for i in all_imports):
        mechanisms.add("OAuth")
    if "django.contrib.auth" in all_imports:
        mechanisms.add("Django auth")
    if all_imports & {"flask_login", "flask-login"}:
        mechanisms.add("Flask-Login")
    if any("spring-security" in i or "springframework.security" in i for i in all_imports):
        mechanisms.add("Spring Security")

    for pf in parsed_files:
        if any(marker in pf.source for marker in _AUTH_CODE_MARKERS):
            if "HTTPBearer" in pf.source or "OAuth2PasswordBearer" in pf.source:
                mechanisms.add("OAuth2/Bearer token")
            if "@UseGuards" in pf.source:
                mechanisms.add("NestJS guards")
            if "[Authorize]" in pf.source:
                mechanisms.add("ASP.NET [Authorize]")
            if "@login_required" in pf.source or "@jwt_required" in pf.source:
                mechanisms.add("Flask decorator-based auth")

    return {"detected": bool(mechanisms), "mechanisms": sorted(mechanisms)}
