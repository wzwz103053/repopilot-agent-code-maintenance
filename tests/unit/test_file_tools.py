from repopilot_agent.tools.file_tools import build_file_tree, scan_code_files, summarize_repo_files


def test_scan_code_files_skips_cache_and_keeps_supported_files(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "main.py").write_text("ignored\n", encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(b"\x00\x01")

    files = scan_code_files(str(tmp_path))

    assert files == ["README.md", "app/main.py"]
    assert "- app/main.py" in build_file_tree(files)
    assert "Found 2 code/document files" in summarize_repo_files(files)
