from app.analyzer.api_surface import detect_api_surface
from app.parser.extractor import parse_source


def test_fastapi_routes_detected():
    src = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def list_users():
    return []

@app.post("/users")
def create_user():
    return {}
'''
    pf = parse_source("main.py", "python", src)
    result = detect_api_surface([pf])

    assert "REST" in result["protocols"]
    methods_paths = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("GET", "/users") in methods_paths
    assert ("POST", "/users") in methods_paths


def test_fastapi_decorator_not_double_counted_as_express():
    src = '@app.get("/users")\ndef list_users():\n    return []\n'
    pf = parse_source("main.py", "python", src)
    result = detect_api_surface([pf])
    assert result["endpoint_count"] == 1


def test_fastapi_websocket_detected():
    src = '@app.websocket("/ws")\ndef ws_endpoint():\n    pass\n'
    pf = parse_source("main.py", "python", src)
    result = detect_api_surface([pf])
    assert "WebSocket" in result["protocols"]


def test_express_routes_detected():
    src = "app.get('/health', (req, res) => res.send('ok'));\nrouter.post('/orders', createOrder);\n"
    pf = parse_source("server.js", "javascript", src)
    result = detect_api_surface([pf])

    methods_paths = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("GET", "/health") in methods_paths
    assert ("POST", "/orders") in methods_paths


def test_spring_routes_detected():
    src = """
@RestController
public class UserController {
    @GetMapping("/api/users")
    public List<User> list() { return null; }
}
"""
    pf = parse_source("UserController.java", "java", src)
    result = detect_api_surface([pf])
    methods_paths = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("GET", "/api/users") in methods_paths


def test_laravel_routes_detected():
    src = "<?php\nRoute::get('/posts', [PostController::class, 'index']);\n"
    pf = parse_source("routes/web.php", "php", src)
    result = detect_api_surface([pf])
    methods_paths = {(e["method"], e["path"]) for e in result["endpoints"]}
    assert ("GET", "/posts") in methods_paths


def test_graphql_detected_from_import():
    pf = parse_source("schema.py", "python", "import graphene\n")
    result = detect_api_surface([pf])
    assert "GraphQL" in result["protocols"]


def test_grpc_detected_from_proto_file():
    pf = parse_source("service.proto", "protobuf", "service Foo {}\n")
    result = detect_api_surface([pf])
    assert "gRPC" in result["protocols"]


def test_auth_detected_from_jwt_import():
    pf = parse_source("auth.py", "python", "import jwt\n")
    result = detect_api_surface([pf])
    assert result["auth"]["detected"] is True
    assert "JWT" in result["auth"]["mechanisms"]


def test_no_endpoints_returns_empty():
    pf = parse_source("main.py", "python", "x = 1\n")
    result = detect_api_surface([pf])
    assert result["endpoints"] == []
    assert result["protocols"] == []
    assert result["auth"]["detected"] is False
