"""Functional and security regression tests for the access plugin.

Tests cover:
- hook.py syntax validation via ast.parse
- Abilities YAML validation
- Security pattern scanning across Python source files
"""
import ast
import os
import glob

import pytest

yaml = pytest.importorskip("yaml")

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestHookSyntax:
    """Verify hook.py can be parsed without syntax errors."""

    def test_hook_parses(self):
        """hook.py should be valid Python syntax."""
        hook_path = os.path.join(PLUGIN_DIR, "hook.py")
        with open(hook_path, encoding='utf-8') as fh:
            source = fh.read()
        tree = ast.parse(source, filename="hook.py")
        assert isinstance(tree, ast.Module)

    def test_hook_has_no_bare_exec(self):
        """hook.py should not contain bare exec() calls."""
        hook_path = os.path.join(PLUGIN_DIR, "hook.py")
        with open(hook_path, encoding='utf-8') as fh:
            source = fh.read()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "exec":
                    pytest.fail("hook.py contains a bare exec() call")

    def test_all_py_files_parse(self):
        """All .py files in the plugin should be valid Python syntax."""
        for root, dirs, files in os.walk(PLUGIN_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath, encoding='utf-8') as fh:
                    source = fh.read()
                try:
                    ast.parse(source, filename=fname)
                except SyntaxError as exc:
                    rel = os.path.relpath(fpath, PLUGIN_DIR)
                    pytest.fail(f"Syntax error in {rel}: {exc}")


class TestAbilitiesYaml:
    """Validate abilities YAML files under data/abilities/."""

    @staticmethod
    def _yaml_files():
        abilities_dir = os.path.join(PLUGIN_DIR, "data", "abilities")
        return glob.glob(os.path.join(abilities_dir, "**", "*.yml"), recursive=True)

    def test_abilities_directory_exists(self):
        """data/abilities/ directory should exist."""
        assert os.path.isdir(os.path.join(PLUGIN_DIR, "data", "abilities"))

    def test_abilities_yaml_files_exist(self):
        """There should be at least one YAML ability file."""
        assert len(self._yaml_files()) > 0, "No .yml files found in data/abilities/"

    def test_abilities_yaml_parseable(self):
        """Each abilities YAML file should be parseable."""
        for yf in self._yaml_files():
            with open(yf, encoding='utf-8') as fh:
                try:
                    list(yaml.safe_load_all(fh))
                except yaml.YAMLError as exc:
                    rel = os.path.relpath(yf, PLUGIN_DIR)
                    pytest.fail(f"YAML parse error in {rel}: {exc}")

    def test_abilities_have_required_fields(self):
        """Each ability must have id, name, and tactic fields."""
        for yf in self._yaml_files():
            with open(yf, encoding='utf-8') as fh:
                docs = list(yaml.safe_load_all(fh))
            for doc in docs:
                if doc is None:
                    continue
                items = doc if isinstance(doc, list) else [doc]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    rel = os.path.relpath(yf, PLUGIN_DIR)
                    assert 'id' in item, f"Missing 'id' in {rel}"
                    assert 'name' in item, f"Missing 'name' in {rel}"
                    assert 'tactic' in item, f"Missing 'tactic' in {rel}"

    def test_abilities_ids_are_unique(self):
        """Ability IDs should not be duplicated within the plugin."""
        seen = {}
        for yf in self._yaml_files():
            with open(yf, encoding='utf-8') as fh:
                docs = list(yaml.safe_load_all(fh))
            for doc in docs:
                if doc is None:
                    continue
                items = doc if isinstance(doc, list) else [doc]
                for item in items:
                    if not isinstance(item, dict) or 'id' not in item:
                        continue
                    aid = item['id']
                    rel = os.path.relpath(yf, PLUGIN_DIR)
                    assert aid not in seen, f"Duplicate ability id {aid} in {rel} and {seen[aid]}"
                    seen[aid] = rel


class TestSecurityPatterns:
    """Scan Python source for risky patterns."""

    @staticmethod
    def _py_files():
        """Collect non-test Python source files."""
        result = []
        for root, dirs, files in os.walk(PLUGIN_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "tests"]
            for fname in files:
                if fname.endswith(".py"):
                    result.append(os.path.join(root, fname))
        return result

    def test_no_verify_false(self):
        """No Python file should use verify=False (disables TLS verification)."""
        for fpath in self._py_files():
            with open(fpath, encoding='utf-8') as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if kw.arg == 'verify' and isinstance(kw.value, ast.Constant) and kw.value.value is False:
                            rel = os.path.relpath(fpath, PLUGIN_DIR)
                            pytest.fail(
                                f"verify=False found at {rel}:{node.lineno}"
                            )

    def test_no_unguarded_shell_true(self):
        """No Python file should use shell=True outside of known-safe patterns."""
        allowlist = {"test_", "conftest.py"}
        for fpath in self._py_files():
            fname = os.path.basename(fpath)
            if any(fname.startswith(a) or fname == a for a in allowlist):
                continue
            with open(fpath, encoding='utf-8') as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    for kw in node.keywords:
                        if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                            rel = os.path.relpath(fpath, PLUGIN_DIR)
                            pytest.fail(
                                f"shell=True found at {rel}:{node.lineno}"
                            )

    def test_requests_have_timeout(self):
        """requests.get/post/put/delete calls should include a timeout parameter."""
        requests_methods = {'get', 'post', 'put', 'delete', 'patch', 'head'}
        for fpath in self._py_files():
            with open(fpath, encoding='utf-8') as fh:
                source = fh.read()
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    is_requests_call = False
                    if isinstance(func, ast.Attribute) and func.attr in requests_methods:
                        if isinstance(func.value, ast.Name) and func.value.id == 'requests':
                            is_requests_call = True
                    if is_requests_call:
                        keyword_names = [kw.arg for kw in node.keywords if kw.arg is not None]
                        if 'timeout' not in keyword_names:
                            rel = os.path.relpath(fpath, PLUGIN_DIR)
                            pytest.fail(
                                f"requests call without timeout at {rel}:{node.lineno}"
                            )
