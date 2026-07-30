from app.analyzer.security import analyze_security
from app.parser.extractor import parse_source


def test_hardcoded_secret_detected():
    pf = parse_source("config.py", "python", 'API_KEY = "sk-1234567890abcdef"\n')
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "hardcoded_secret" in categories


def test_env_var_lookup_not_flagged():
    pf = parse_source("config.py", "python", 'API_KEY = os.environ["API_KEY"]\n')
    result = analyze_security([pf])
    assert result["findings"] == []


def test_placeholder_value_not_flagged():
    pf = parse_source("config.py", "python", 'password = "changeme"\n')
    result = analyze_security([pf])
    assert result["findings"] == []


def test_aws_key_detected():
    pf = parse_source("config.py", "python", 'key = "AKIAABCDEFGHIJKLMNOP"\n')
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "hardcoded_secret" in categories


def test_sql_injection_fstring_detected():
    pf = parse_source("db.py", "python", 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "sql_injection" in categories


def test_parameterized_query_not_flagged():
    pf = parse_source("db.py", "python", 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))\n')
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "sql_injection" not in categories


def test_pickle_loads_detected():
    pf = parse_source("cache.py", "python", "data = pickle.loads(raw)\n")
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "unsafe_deserialization" in categories


def test_yaml_load_without_safe_loader_detected():
    pf = parse_source("cfg.py", "python", "data = yaml.load(f)\n")
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "unsafe_deserialization" in categories


def test_yaml_safe_load_not_flagged():
    pf = parse_source("cfg.py", "python", "data = yaml.load(f, Loader=yaml.SafeLoader)\n")
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "unsafe_deserialization" not in categories


def test_md5_password_hash_detected():
    pf = parse_source("auth.py", "python", "hashed_password = md5(password).hexdigest()\n")
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "weak_auth" in categories


def test_sensitive_log_detected():
    pf = parse_source("app.py", "python", 'logger.info(f"login attempt with password={password}")\n')
    result = analyze_security([pf])
    categories = {f["category"] for f in result["findings"]}
    assert "sensitive_log" in categories


def test_clean_file_has_no_findings():
    pf = parse_source("app.py", "python", "def add(a, b):\n    return a + b\n")
    result = analyze_security([pf])
    assert result["findings"] == []
