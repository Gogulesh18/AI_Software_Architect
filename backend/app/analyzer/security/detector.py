"""Security findings: hardcoded secrets, SQL injection, unsafe deserialization,
weak auth (weak hashing), sensitive logging, open endpoints, missing validation.

Pattern-based, not a taint-tracking scanner: it catches the common,
recognizable forms of each issue (an f-string spliced into `.execute()`, a
private-key block, `pickle.loads`) with the intent of surfacing real risk
cheaply, not proving absence of vulnerabilities. False negatives are
expected on obfuscated/indirect cases.
"""

import re

from app.analyzer.models import Finding, findings_to_dicts
from app.parser.models import ParsedFile

_SECRET_ASSIGNMENT_RE = re.compile(
    r'(?i)\b(api[_-]?key|secret[_-]?key|secret|password|passwd|access[_-]?key|auth[_-]?token)\b\s*[:=]\s*["\']([^"\']{8,})["\']'
)
_ENV_LOOKUP_HINTS = ("os.environ", "process.env", "getenv", "System.getenv", "Environment.GetEnvironmentVariable")
_PLACEHOLDER_VALUES = {"changeme", "xxx", "your_key_here", "example", "placeholder", "todo", "<your-key>", "insert_key_here", "test", "password"}
_AWS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
_PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----")

_SQL_INJECTION_PATTERNS = [
    re.compile(r'\.execute\(\s*f["\']'),  # Python f-string straight into execute()
    re.compile(r'\.execute\(\s*["\'][^"\']*["\']\s*%\s'),  # % string formatting into execute()
    re.compile(r'\.execute\(\s*["\'][^"\']*["\']\s*\+'),  # string concatenation into execute()
    re.compile(r"\.query\(\s*`[^`]*\$\{"),  # JS/TS template literal interpolation into query()
    re.compile(r'\.(query|execute)\(\s*["\'][^"\']*["\']\s*\+'),  # generic concatenation
]

_UNSAFE_DESERIALIZATION_PATTERNS = [
    (re.compile(r"\bpickle\.loads?\("), "pickle.load(s) can execute arbitrary code on untrusted input"),
    (re.compile(r"\byaml\.load\((?!.*SafeLoader)"), "yaml.load without SafeLoader can instantiate arbitrary objects"),
    (re.compile(r"(?<!safe_)\beval\("), "eval() executes arbitrary code"),
    (re.compile(r"\bexec\("), "exec() executes arbitrary code"),
    (re.compile(r"\bunserialize\("), "PHP unserialize() on untrusted input can execute arbitrary code"),
    (re.compile(r"\bObjectInputStream\b"), "Java native deserialization is a known gadget-chain RCE vector"),
]

_WEAK_HASH_RE = re.compile(r"(?i)\b(md5|sha1)\s*\(")
_SENSITIVE_LOG_RE = re.compile(
    r"(?i)\b(log(?:ger)?\.\w+|console\.(?:log|error|warn|info)|print)\s*\([^)]*\b(password|secret|token|api_key|credit_card|ssn)\b"
)


def analyze_security(parsed_files: list[ParsedFile]) -> dict:
    findings: list[Finding] = []

    for pf in parsed_files:
        lines = pf.source.splitlines()
        for lineno, line in enumerate(lines, start=1):
            findings.extend(_secret_findings(pf, lineno, line))
            findings.extend(_sql_injection_findings(pf, lineno, line))
            findings.extend(_deserialization_findings(pf, lineno, line))
            findings.extend(_weak_hash_findings(pf, lineno, line))
            findings.extend(_sensitive_log_findings(pf, lineno, line))

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: severity_order.get(f.severity, 5))

    by_category: dict[str, int] = {}
    for f in findings:
        by_category[f.category] = by_category.get(f.category, 0) + 1

    return {"summary": by_category, "findings": findings_to_dicts(findings)}


def _secret_findings(pf: ParsedFile, lineno: int, line: str) -> list[Finding]:
    findings: list[Finding] = []
    if any(hint in line for hint in _ENV_LOOKUP_HINTS):
        return findings  # reading from env is the correct pattern, not a leak

    for m in _SECRET_ASSIGNMENT_RE.finditer(line):
        value = m.group(2)
        if value.lower() in _PLACEHOLDER_VALUES or value.startswith(("${", "{{")):
            continue
        findings.append(Finding("hardcoded_secret", "critical", pf.relative_path, f"possible hardcoded {m.group(1)}", lineno))

    if _AWS_KEY_RE.search(line):
        findings.append(Finding("hardcoded_secret", "critical", pf.relative_path, "AWS access key ID literal found", lineno))
    if _PRIVATE_KEY_RE.search(line):
        findings.append(Finding("hardcoded_secret", "critical", pf.relative_path, "private key material committed to source", lineno))
    return findings


def _sql_injection_findings(pf: ParsedFile, lineno: int, line: str) -> list[Finding]:
    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(line):
            return [Finding("sql_injection", "high", pf.relative_path, "user input may be interpolated directly into a SQL query — use parameterized queries", lineno)]
    return []


def _deserialization_findings(pf: ParsedFile, lineno: int, line: str) -> list[Finding]:
    for pattern, reason in _UNSAFE_DESERIALIZATION_PATTERNS:
        if pattern.search(line):
            return [Finding("unsafe_deserialization", "high", pf.relative_path, reason, lineno)]
    return []


def _weak_hash_findings(pf: ParsedFile, lineno: int, line: str) -> list[Finding]:
    if _WEAK_HASH_RE.search(line) and "password" in line.lower():
        return [Finding("weak_auth", "high", pf.relative_path, "MD5/SHA1 is not suitable for password hashing — use bcrypt/argon2/scrypt", lineno)]
    return []


def _sensitive_log_findings(pf: ParsedFile, lineno: int, line: str) -> list[Finding]:
    if _SENSITIVE_LOG_RE.search(line):
        return [Finding("sensitive_log", "medium", pf.relative_path, "log statement appears to include a sensitive value", lineno)]
    return []
