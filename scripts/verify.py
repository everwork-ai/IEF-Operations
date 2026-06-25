#!/usr/bin/env python3
"""
IEF Verification Module - Minimal Validator Interface

This module provides the minimal implementation of the IEF verification system:
- Schema validation for VerificationRequest, VerificationResult, VerificationEvidence
- Fixture-based test runner (no production verifier daemon)
- Result object validation with result/severity constraint enforcement

Usage:
    python verify.py --validate-request <path>
    python verify.py --validate-result <path>
    python verify.py --validate-evidence <path>
    python verify.py --run-fixtures [--fixtures-dir <path>]

Author: ief-operator
License: MIT
"""

import json
import sys
import io
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

# Force UTF-8 output on Windows to avoid cp1252 encoding errors with emoji
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Try to import jsonschema; if not available, use basic validation
try:
    import jsonschema
    from jsonschema import Draft202012Validator, ValidationError
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    print("Warning: jsonschema not installed. Using basic validation only.", file=sys.stderr)


# Schema paths (relative to this script: scripts/ -> repo root)
SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures" / "verification"


def load_schema(schema_name: str) -> dict:
    """Load a JSON Schema file from the schemas directory."""
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_json(path: Path) -> dict:
    """Load a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_against_schema(instance: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    Validate a JSON instance against a schema.
    
    Returns:
        (valid, errors) where valid is True if instance matches schema,
        and errors is a list of error messages.
    """
    if not HAS_JSONSCHEMA:
        # Basic validation: check required fields
        required = schema.get("required", [])
        errors = []
        for field in required:
            if field not in instance:
                errors.append(f"Missing required field: {field}")
        return len(errors) == 0, errors
    
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(instance))
    
    if not errors:
        return True, []
    
    error_messages = []
    for error in errors:
        path = ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        error_messages.append(f"{path}: {error.message}")
    
    return False, error_messages


def validate_request(request: dict) -> tuple[bool, list[str]]:
    """Validate a VerificationRequest against the schema."""
    schema = load_schema("verification_request.schema.json")
    return validate_against_schema(request, schema)


def validate_result(result: dict) -> tuple[bool, list[str]]:
    """Validate a VerificationResult against the schema."""
    schema = load_schema("verification_result.schema.json")
    return validate_against_schema(result, schema)


def validate_evidence(evidence: dict) -> tuple[bool, list[str]]:
    """Validate a VerificationEvidence against the schema."""
    schema = load_schema("verification_evidence.schema.json")
    return validate_against_schema(evidence, schema)


def validate_ledger_event(event: dict) -> tuple[bool, list[str]]:
    """Validate a ledger entry against the schema."""
    schema = load_schema("ledger_entry.schema.json")
    return validate_against_schema(event, schema)


def check_result_severity_constraint(result: str, severity: str) -> tuple[bool, str]:
    """
    Check the result/severity constraint:
    - pass -> info only
    - fail -> error or critical
    - conditional -> warning only
    - skipped -> info only
    
    Returns:
        (valid, reason) where valid is True if constraint is satisfied.
    """
    constraints = {
        "pass": ["info"],
        "fail": ["error", "critical"],
        "conditional": ["warning"],
        "skipped": ["info"],
    }
    
    if result not in constraints:
        return False, f"Unknown result value: {result}"
    
    allowed = constraints[result]
    if severity not in allowed:
        return False, f"result '{result}' requires severity in {allowed}, got '{severity}'"
    
    return True, "OK"


def check_overall_constraint(overall_result: str, overall_severity: str) -> tuple[bool, str]:
    """
    Check the overall result/severity constraint:
    - pass -> info
    - fail -> error or critical
    - conditional -> warning
    - blocked -> any (warning typical)
    
    Returns:
        (valid, reason)
    """
    constraints = {
        "pass": ["info"],
        "fail": ["error", "critical"],
        "conditional": ["warning"],
        "blocked": ["info", "warning", "error", "critical"],  # blocked is special case
    }
    
    if overall_result not in constraints:
        return False, f"Unknown overall_result value: {overall_result}"
    
    allowed = constraints[overall_result]
    if overall_severity not in allowed:
        return False, f"overall_result '{overall_result}' requires overall_severity in {allowed}, got '{overall_severity}'"
    
    return True, "OK"


def run_fixture_test(fixture_path: Path) -> tuple[bool, str]:
    """
    Run a single fixture test.
    
    Each fixture JSON has:
    - request: VerificationRequest input
    - expected_result: VerificationResult expected output
    - test_id: test identifier
    - description: test description
    
    Or for ledger event fixtures:
    - ledger_event: ledger entry fixture
    - test_id: test identifier
    - description: test description
    
    Returns:
        (passed, message)
    """
    fixture = load_json(fixture_path)
    test_id = fixture.get("test_id", fixture_path.stem)
    description = fixture.get("description", "")
    
    print(f"\n{'='*70}")
    print(f"Test {test_id}: {description}")
    print(f"{'='*70}")
    
    # Case 1: Ledger event fixture
    if "ledger_event" in fixture:
        event = fixture["ledger_event"]
        valid, errors = validate_ledger_event(event)
        if not valid:
            print(f"❌ FAIL: Ledger event validation failed")
            for error in errors:
                print(f"   - {error}")
            return False, "Ledger event validation failed"
        
        print(f"✅ PASS: Ledger event validates against schema")
        return True, "OK"
    
    # Case 2: Request/Result fixture
    if "request" not in fixture or "expected_result" not in fixture:
        print(f"❌ FAIL: Fixture missing 'request' or 'expected_result'")
        return False, "Invalid fixture structure"
    
    request = fixture["request"]
    expected = fixture["expected_result"]
    
    # Validate request
    req_valid, req_errors = validate_request(request)
    if not req_valid:
        print(f"❌ FAIL: Request validation failed")
        for error in req_errors:
            print(f"   - {error}")
        return False, "Request validation failed"
    
    print(f"✅ Request validates against schema")
    
    # Validate expected result
    res_valid, res_errors = validate_result(expected)
    if not res_valid:
        print(f"❌ FAIL: Expected result validation failed")
        for error in res_errors:
            print(f"   - {error}")
        return False, "Expected result validation failed"
    
    print(f"✅ Expected result validates against schema")
    
    # Check result/severity constraints at dimension level
    for dim in expected.get("dimensions_verified", []):
        result = dim.get("result")
        severity = dim.get("severity")
        if result and severity:
            constraint_valid, reason = check_result_severity_constraint(result, severity)
            if not constraint_valid:
                print(f"❌ FAIL: Dimension {dim.get('dimension')} constraint violation: {reason}")
                return False, f"Dimension constraint violation: {reason}"
    
    print(f"✅ Dimension result/severity constraints satisfied")
    
    # Check overall result/severity constraint
    overall_result = expected.get("overall_result")
    overall_severity = expected.get("overall_severity")
    if overall_result and overall_severity:
        overall_valid, reason = check_overall_constraint(overall_result, overall_severity)
        if not overall_valid:
            print(f"❌ FAIL: Overall constraint violation: {reason}")
            return False, f"Overall constraint violation: {reason}"
    
    print(f"✅ Overall result/severity constraint satisfied")
    
    # Check blocked reason requirement
    if overall_result == "blocked":
        blocked_reason = expected.get("blocked_reason")
        if not blocked_reason:
            print(f"❌ FAIL: blocked result requires blocked_reason")
            return False, "Missing blocked_reason"
        print(f"✅ Blocked reason present: {blocked_reason}")
    
    # Check critical -> retry_eligible=false constraint
    if overall_severity == "critical":
        retry_eligible = expected.get("retry_eligible")
        if retry_eligible is True:
            print(f"❌ FAIL: critical severity requires retry_eligible=false")
            return False, "Critical severity must have retry_eligible=false"
        print(f"✅ Critical severity correctly has retry_eligible=false")
    
    print(f"✅ PASS: All constraints satisfied")
    return True, "OK"


def run_all_fixtures(fixtures_dir: Optional[Path] = None) -> tuple[int, int]:
    """
    Run all fixture tests in the given directory.
    
    Returns:
        (passed_count, failed_count)
    """
    fixtures_dir = fixtures_dir or FIXTURES_DIR
    
    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory not found: {fixtures_dir}", file=sys.stderr)
        return 0, 0
    
    fixture_files = sorted(fixtures_dir.glob("*.json"))
    
    if not fixture_files:
        print(f"No fixture files found in {fixtures_dir}", file=sys.stderr)
        return 0, 0
    
    print(f"Running {len(fixture_files)} fixture tests from {fixtures_dir}")
    
    passed = 0
    failed = 0
    
    for fixture_path in fixture_files:
        try:
            test_passed, message = run_fixture_test(fixture_path)
            if test_passed:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ ERROR running {fixture_path.name}: {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"RESULTS: {passed} passed, {failed} failed, {len(fixture_files)} total")
    print(f"{'='*70}\n")
    
    return passed, failed


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="IEF Verification Module Validator")
    parser.add_argument("--validate-request", metavar="PATH", help="Validate a VerificationRequest JSON file")
    parser.add_argument("--validate-result", metavar="PATH", help="Validate a VerificationResult JSON file")
    parser.add_argument("--validate-evidence", metavar="PATH", help="Validate a VerificationEvidence JSON file")
    parser.add_argument("--validate-ledger", metavar="PATH", help="Validate a ledger entry JSON file")
    parser.add_argument("--run-fixtures", action="store_true", help="Run all fixture tests")
    parser.add_argument("--fixtures-dir", metavar="PATH", help="Directory containing fixture files (default: tests/fixtures/verification)")
    
    args = parser.parse_args()
    
    if args.validate_request:
        data = load_json(Path(args.validate_request))
        valid, errors = validate_request(data)
        if valid:
            print("✅ VerificationRequest is valid")
            sys.exit(0)
        else:
            print("❌ VerificationRequest validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    elif args.validate_result:
        data = load_json(Path(args.validate_result))
        valid, errors = validate_result(data)
        if valid:
            print("✅ VerificationResult is valid")
            sys.exit(0)
        else:
            print("❌ VerificationResult validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    elif args.validate_evidence:
        data = load_json(Path(args.validate_evidence))
        valid, errors = validate_evidence(data)
        if valid:
            print("✅ VerificationEvidence is valid")
            sys.exit(0)
        else:
            print("❌ VerificationEvidence validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    elif args.validate_ledger:
        data = load_json(Path(args.validate_ledger))
        valid, errors = validate_ledger_event(data)
        if valid:
            print("✅ Ledger entry is valid")
            sys.exit(0)
        else:
            print("❌ Ledger entry validation failed:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
    
    elif args.run_fixtures:
        fixtures_dir = Path(args.fixtures_dir) if args.fixtures_dir else None
        passed, failed = run_all_fixtures(fixtures_dir)
        sys.exit(0 if failed == 0 else 1)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
