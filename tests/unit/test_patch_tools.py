from repopilot_agent.tools.patch_tools import (
    apply_unified_diff,
    build_unified_diff,
    extract_modified_files_from_diff,
    validate_unified_diff,
)


def test_build_validate_and_apply_unified_diff(tmp_path):
    source = tmp_path / "app" / "service.py"
    source.parent.mkdir()
    before = "def message():\n    return 'old'\n"
    after = "def message():\n    return 'new'\n"
    source.write_text(before, encoding="utf-8")

    diff = build_unified_diff("app/service.py", before, after)

    is_valid, errors = validate_unified_diff(diff)
    result = apply_unified_diff(str(tmp_path), diff)

    assert is_valid is True
    assert errors == []
    assert extract_modified_files_from_diff(diff) == ["app/service.py"]
    assert result["patch_status"] == "applied"
    assert source.read_text(encoding="utf-8") == after


def test_validate_unified_diff_rejects_empty_patch():
    is_valid, errors = validate_unified_diff("")

    assert is_valid is False
    assert "Patch diff is empty." in errors
