"""
Test Suite: Architectural Layer Dependency Isolation
Verifies that app.domain has ZERO forbidden imports:
- No FastAPI
- No SQLAlchemy
- No Pydantic
- No Anny
- No PyTorch
"""

import ast
import os
import pytest

FORBIDDEN_MODULES = {"fastapi", "sqlalchemy", "pydantic", "anny", "torch"}


def get_all_python_files(directory: str):
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files


def test_domain_layer_isolation():
    """Parse all ASTs in app/domain and verify no forbidden imports exist."""
    domain_dir = os.path.join(os.path.dirname(__file__), "..", "..", "app", "domain")
    domain_dir = os.path.abspath(domain_dir)
    assert os.path.exists(domain_dir), f"Domain directory {domain_dir} does not exist"

    py_files = get_all_python_files(domain_dir)
    assert len(py_files) > 0, "No domain python files found to test"

    violations = []

    for file_path in py_files:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_module = alias.name.split(".")[0]
                    if top_module in FORBIDDEN_MODULES:
                        violations.append((file_path, node.lineno, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_module = node.module.split(".")[0]
                    if top_module in FORBIDDEN_MODULES:
                        violations.append((file_path, node.lineno, node.module))

    assert not violations, (
        f"Found forbidden architectural imports in domain layer:\n"
        + "\n".join(f"  {path}:{lineno} -> import '{mod}'" for path, lineno, mod in violations)
    )
