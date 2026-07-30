from app.parser.extractor import parse_source


def test_nesting_depth_measures_deepest_branch():
    src = """
def flat():
    if True:
        pass

def nested():
    if True:
        for x in range(10):
            if x:
                pass
"""
    result = parse_source("a.py", "python", src)
    flat = next(s for s in result.functions if s.name == "flat")
    nested = next(s for s in result.functions if s.name == "nested")
    assert flat.max_nesting_depth == 1
    assert nested.max_nesting_depth == 3


def test_source_is_retained_on_parsed_file():
    result = parse_source("a.py", "python", "x = 1\n")
    assert result.source == "x = 1\n"
    assert result.line(1) == "x = 1"
