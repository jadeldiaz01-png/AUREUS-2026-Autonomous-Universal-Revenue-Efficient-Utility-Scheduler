import importlib.util
from pathlib import Path


def load_module():
    path = Path(__file__).parents[1] / "scripts" / "collect_runtime_evidence.py"
    spec = importlib.util.spec_from_file_location("collect_runtime_evidence", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_verified_section_requires_every_assertion():
    module = load_module()
    section = module.verified_section({"a": True, "b": True}, ("a", "b"))
    assert section["verified"] is True
    assert section["evidence_ref"].startswith("sha256:")

    blocked = module.verified_section({"a": True, "b": False}, ("a", "b"))
    assert blocked["verified"] is False


def test_canonical_hash_is_deterministic():
    module = load_module()
    assert module.canonical_sha256({"b": 2, "a": 1}) == module.canonical_sha256({"a": 1, "b": 2})
