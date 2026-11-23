"""
Test Suite: BICE Architectural Layer Isolation
Inspects app/bice module AST to guarantee zero prohibited imports
(torch, avatar_engine, canny, mesh_eval, etc.) ensuring complete engine independence.
"""

import ast
from pathlib import Path
import pytest

BICE_PACKAGE_PATH = Path(__file__).resolve().parent.parent.parent / "app" / "bice"

PROHIBITED_MODULES = {
    "torch",
    "torchvision",
    "scipy",
    "avatar_engine",
    "canny",
    "mesh_eval",
    "sqlalchemy",
    "fastapi",
}


def test_bice_prohibited_imports_ast():
    """
    Statically analyzes all Python files in app/bice/ to guarantee that no
    prohibited or engine-coupled packages are imported.
    """
    assert BICE_PACKAGE_PATH.exists(), f"Path not found: {BICE_PACKAGE_PATH}"

    python_files = list(BICE_PACKAGE_PATH.glob("*.py"))
    assert len(python_files) >= 7, f"Expected at least 7 files in app/bice, found {len(python_files)}"

    violations = []

    for py_file in python_files:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    if root_pkg in PROHIBITED_MODULES:
                        violations.append((py_file.name, root_pkg, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    if root_pkg in PROHIBITED_MODULES:
                        violations.append((py_file.name, root_pkg, node.lineno))

    assert len(violations) == 0, f"Prohibited architectural imports detected in app/bice: {violations}"
