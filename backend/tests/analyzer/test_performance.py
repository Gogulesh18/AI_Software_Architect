from app.analyzer.performance import analyze_performance
from app.parser.extractor import parse_source


def test_n_plus_one_detected():
    src = """
def list_orders(users):
    for user in users:
        orders = db.query(Order).filter(Order.user_id == user.id).all()
    return orders
"""
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "n_plus_one_query" in categories


def test_no_n_plus_one_when_query_outside_loop():
    src = """
def list_orders():
    orders = db.query(Order).all()
    for order in orders:
        print(order)
"""
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "n_plus_one_query" not in categories


def test_blocking_call_in_async_function_detected():
    src = """
async def handler():
    time.sleep(5)
    return "done"
"""
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "blocking_call" in categories


def test_nested_loops_detected_as_expensive():
    src = """
def compare_all(items):
    for a in items:
        for b in items:
            if a == b:
                pass
"""
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "expensive_loop" in categories


def test_single_loop_not_flagged_expensive():
    src = "def f(items):\n    for x in items:\n        print(x)\n"
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "expensive_loop" not in categories


def test_repeated_call_without_cache_detected():
    src = """
def compute():
    a = fetch_data()
    b = fetch_data()
    c = fetch_data()
    return a + b + c
"""
    pf = parse_source("a.py", "python", src)
    result = analyze_performance([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "missing_cache" in categories


def test_clean_function_has_no_findings():
    pf = parse_source("a.py", "python", "def add(a, b):\n    return a + b\n")
    result = analyze_performance([pf])
    assert result["findings"] == []
