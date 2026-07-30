from app.parser.extractor import parse_source


def test_go_extraction():
    src = """
package main

import "fmt"

type User struct {
	Name string
}

func (u *User) Save() error {
	if u.Name == "" {
		return fmt.Errorf("empty")
	}
	return nil
}

func main() {
	fmt.Println("hi")
}
"""
    result = parse_source("main.go", "go", src)
    assert "fmt" in result.imports
    assert {s.name for s in result.classes} == {"User"}
    save = next(s for s in result.functions if s.name == "Save")
    assert save.complexity == 2


def test_rust_extraction():
    src = """
use std::collections::HashMap;

struct User { name: String }

impl User {
    fn save(&self) {
        println!("saved");
    }
}

fn main() {}
"""
    result = parse_source("main.rs", "rust", src)
    assert "std::collections::HashMap" in result.imports
    assert {s.name for s in result.classes} >= {"User"}
    assert any(s.name == "save" for s in result.functions)


def test_csharp_extraction_with_attributes():
    src = """
using System;

[ApiController]
public class UserController {
    [HttpGet]
    public void List() {}
}
"""
    result = parse_source("UserController.cs", "csharp", src)
    controller = result.classes[0]
    assert any("ApiController" in d for d in controller.decorators)
    method = result.functions[0]
    assert any("HttpGet" in d for d in method.decorators)


def test_php_extraction_with_attributes():
    src = """<?php
namespace App;
use App\\Models\\User;

class UserController {
    #[Route("/users")]
    public function list() {}
}
"""
    result = parse_source("UserController.php", "php", src)
    assert result.imports
    method = result.functions[0]
    assert any("Route" in d for d in method.decorators)


def test_cpp_extraction():
    src = """
#include <iostream>

class Repository : public Base {
public:
    void save() {}
};

int add(int a, int b) {
    if (a > b) { return a; }
    return b;
}
"""
    result = parse_source("repo.cpp", "cpp", src)
    assert "iostream" in result.imports
    assert {s.name for s in result.classes} == {"Repository"}
    add = next(s for s in result.functions if s.name == "add")
    assert add.complexity == 2
