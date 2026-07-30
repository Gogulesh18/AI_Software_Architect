from app.parser.extractor import parse_source


def test_python_extraction():
    src = '''
import os
from typing import List

@app.get("/users")
def list_users():
    if True:
        pass
    return []


class UserRepository:
    def find(self, id):
        return db.query(id)
'''
    result = parse_source("app.py", "python", src)
    assert result.imports == ["os", "typing"]
    assert {s.name for s in result.classes} == {"UserRepository"}
    assert {s.name for s in result.functions} == {"list_users", "find"}

    list_users = next(s for s in result.functions if s.name == "list_users")
    assert list_users.decorators == ['@app.get("/users")']
    assert list_users.complexity == 2  # base 1 + one if

    find = next(s for s in result.functions if s.name == "find")
    assert find.parent_class == "UserRepository"
    assert "db.query" in find.calls


def test_javascript_extraction():
    src = """
import React from "react";
import { useState } from "react";

class UserService {
  fetchAll() {
    return fetch("/api/users");
  }
}

function main() {
  const svc = new UserService();
}
"""
    result = parse_source("app.js", "javascript", src)
    assert "react" in result.imports
    assert {s.name for s in result.classes} == {"UserService"}
    assert {s.name for s in result.functions} == {"fetchAll", "main"}


def test_java_extraction_with_annotations():
    src = """
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {
    @GetMapping("/users")
    public void list() {}
}
"""
    result = parse_source("UserController.java", "java", src)
    controller = result.classes[0]
    assert controller.name == "UserController"
    assert any("RestController" in d for d in controller.decorators)
    method = result.functions[0]
    assert method.parent_class == "UserController"
    assert any("GetMapping" in d for d in method.decorators)


def test_unknown_language_returns_shallow_result():
    result = parse_source("data.txt", "text", "hello\nworld\n")
    assert result.symbols == []
    assert result.imports == []
    assert result.loc == 2


def test_parse_error_does_not_raise():
    # Malformed source should still produce a best-effort partial tree, not crash.
    result = parse_source("broken.py", "python", "def foo(:\n")
    assert result.language == "python"
