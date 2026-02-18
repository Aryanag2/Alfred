"""Tests for the dispatch and execute agent commands."""

import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

import alfred

runner = CliRunner()


# ============================================================
# Agent prompt loading
# ============================================================

class TestLoadAgentPrompt:
    """Test _load_agent_prompt and _find_agents_dir."""

    def test_load_existing_agent_prompt(self):
        """Should load the .md file for a known agent."""
        prompt = alfred._load_agent_prompt("convert")
        assert len(prompt) > 0
        # Should contain some instruction-like content, not the fallback
        assert "JSON" in prompt or "convert" in prompt.lower()

    def test_load_all_five_agents(self):
        """Every shipped agent prompt file should be loadable."""
        for name in ("convert", "organize", "summarize", "rename", "command"):
            prompt = alfred._load_agent_prompt(name)
            assert len(prompt) > 50, f"Agent '{name}' prompt is suspiciously short"

    def test_load_missing_agent_returns_fallback(self):
        """An unknown agent name should return a sensible fallback string."""
        prompt = alfred._load_agent_prompt("nonexistent_agent_xyz")
        assert "nonexistent_agent_xyz" in prompt
        assert "JSON" in prompt

    def test_find_agents_dir_env_override(self, tmp_path, monkeypatch):
        """ALFRED_AGENTS_DIR env var should take precedence."""
        agents = tmp_path / "custom_agents"
        agents.mkdir()
        (agents / "convert.md").write_text("custom prompt")
        monkeypatch.setenv("ALFRED_AGENTS_DIR", str(agents))

        prompt = alfred._load_agent_prompt("convert")
        assert prompt == "custom prompt"

    def test_find_agents_dir_ignores_bad_env(self, monkeypatch):
        """If env var points to a non-existent dir, fall back gracefully."""
        monkeypatch.setenv("ALFRED_AGENTS_DIR", "/nonexistent/path/agents")
        prompt = alfred._load_agent_prompt("convert")
        # Should still load the real prompt (from the sibling agents/ dir)
        assert len(prompt) > 50


# ============================================================
# Build dispatch context
# ============================================================

class TestBuildDispatchContext:
    """Test _build_dispatch_context."""

    def test_includes_query(self):
        ctx = alfred._build_dispatch_context("convert", "make this a pdf", [])
        assert "make this a pdf" in ctx

    def test_includes_file_info(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("world")
        ctx = alfred._build_dispatch_context("convert", "convert it", [str(f)])
        assert "hello.txt" in ctx
        assert "FILE:" in ctx

    def test_includes_folder_contents(self, tmp_path):
        (tmp_path / "a.png").write_bytes(b"img")
        (tmp_path / "b.txt").write_text("txt")
        ctx = alfred._build_dispatch_context("organize", "sort by type", [str(tmp_path)])
        assert "FOLDER:" in ctx
        assert "a.png" in ctx

    def test_missing_path_noted(self):
        ctx = alfred._build_dispatch_context("convert", "convert it", ["/no/such/file.txt"])
        assert "not found" in ctx

    def test_hidden_files_excluded_from_folder(self, tmp_path):
        (tmp_path / ".hidden").write_bytes(b"secret")
        (tmp_path / "visible.txt").write_text("hi")
        ctx = alfred._build_dispatch_context("organize", "sort", [str(tmp_path)])
        assert ".hidden" not in ctx
        assert "visible.txt" in ctx


# ============================================================
# Dispatch command (CLI integration)
# ============================================================

class TestDispatchCommand:
    """Test the dispatch CLI command."""

    def test_invalid_agent_name(self):
        result = runner.invoke(alfred.app, ["dispatch", "bogus_agent", "do something"])
        assert result.exit_code == 1
        assert "Unknown agent" in result.stdout

    def test_dispatch_returns_json(self, mock_ollama):
        """dispatch should return valid JSON to stdout."""
        plan = {"action": "convert", "input_file": "/tmp/a.png", "target_format": "jpg", "explanation": "Convert PNG to JPG"}
        mock_ollama(json.dumps(plan))

        result = runner.invoke(alfred.app, ["dispatch", "convert", "make this a jpg", "/tmp/a.png"])
        assert result.exit_code == 0

        parsed = json.loads(result.stdout.strip())
        assert parsed["action"] == "convert"
        assert "explanation" in parsed

    def test_dispatch_handles_markdown_fenced_json(self, mock_ollama):
        """If the LLM wraps JSON in ```json ... ```, dispatch should strip it."""
        plan = {"action": "none", "explanation": "nothing to do"}
        mock_ollama(f"```json\n{json.dumps(plan)}\n```")

        result = runner.invoke(alfred.app, ["dispatch", "convert", "hello"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout.strip())
        assert parsed["action"] == "none"

    def test_dispatch_wraps_non_json_response(self, mock_ollama):
        """If the LLM returns plain text, dispatch should wrap it in a fallback JSON."""
        mock_ollama("Unclear request.")

        result = runner.invoke(alfred.app, ["dispatch", "convert", "asdfghjkl"])
        assert result.exit_code == 0
        parsed = json.loads(result.stdout.strip())
        assert parsed["action"] == "none"
        assert "explanation" in parsed

    def test_dispatch_all_valid_agents(self, mock_ollama):
        """Every valid agent name should be accepted without error."""
        plan = {"action": "none", "explanation": "test"}
        mock_ollama(json.dumps(plan))

        for agent in ("convert", "organize", "summarize", "rename", "command"):
            result = runner.invoke(alfred.app, ["dispatch", agent, "test query"])
            assert result.exit_code == 0, f"Agent '{agent}' dispatch failed"


# ============================================================
# Execute command (CLI integration)
# ============================================================

class TestExecuteCommand:
    """Test the execute CLI command."""

    def test_invalid_json(self):
        result = runner.invoke(alfred.app, ["execute", "not json at all"])
        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout

    def test_action_none(self):
        plan = {"action": "none", "explanation": "Nothing to do."}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert "Nothing to do" in result.stdout

    def test_unknown_action(self):
        plan = {"action": "teleport", "explanation": "impossible"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 1
        assert "Unknown action" in result.stdout

    # --- Convert action ---

    def test_execute_convert(self, tmp_path):
        """Execute a convert plan — uses the real convert pipeline for data formats."""
        input_file = tmp_path / "data.json"
        input_file.write_text('[{"name": "Alice", "age": 30}]')

        plan = {
            "action": "convert",
            "input_file": str(input_file),
            "target_format": "csv",
            "explanation": "Convert JSON to CSV"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert (tmp_path / "data.csv").exists()

    def test_execute_convert_missing_fields(self):
        plan = {"action": "convert", "explanation": "no file"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 1
        assert "missing" in result.stdout.lower() or "Error" in result.stdout

    # --- Organize action ---

    def test_execute_organize(self, tmp_path):
        """Execute an organize plan — moves files into subfolders."""
        (tmp_path / "photo.jpg").write_bytes(b"img")
        (tmp_path / "song.mp3").write_bytes(b"audio")

        plan = {
            "action": "organize",
            "folder": str(tmp_path),
            "plan": {
                "Images": ["photo.jpg"],
                "Music": ["song.mp3"]
            },
            "explanation": "Sort by type"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert (tmp_path / "Images" / "photo.jpg").exists()
        assert (tmp_path / "Music" / "song.mp3").exists()
        assert "Moved 2" in result.stdout

    def test_execute_organize_skips_missing_files(self, tmp_path):
        plan = {
            "action": "organize",
            "folder": str(tmp_path),
            "plan": {"Docs": ["nonexistent.pdf"]},
            "explanation": "sort"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert "Moved 0" in result.stdout

    def test_execute_organize_missing_plan(self, tmp_path):
        plan = {"action": "organize", "folder": str(tmp_path)}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 1

    # --- Summarize action ---

    def test_execute_summarize(self, tmp_path, mock_ollama):
        f = tmp_path / "readme.txt"
        f.write_text("Alfred is a file management assistant.")
        mock_ollama("Summary: Alfred is a helper app.")

        plan = {
            "action": "summarize",
            "files": [str(f)],
            "style": "brief",
            "explanation": "Summarize the readme"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert "Summarizing" in result.stdout or "Summary" in result.stdout

    def test_execute_summarize_no_files(self):
        plan = {"action": "summarize", "files": [], "explanation": "nothing"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 1 or "No" in result.stdout

    # --- Rename action ---

    def test_execute_rename(self, tmp_path):
        old = tmp_path / "IMG_001.jpg"
        old.write_bytes(b"photo")

        plan = {
            "action": "rename",
            "renames": {str(old): "sunset_photo.jpg"},
            "explanation": "Descriptive rename"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert (tmp_path / "sunset_photo.jpg").exists()
        assert not old.exists()
        assert "Renamed 1" in result.stdout

    def test_execute_rename_skips_missing(self, tmp_path):
        plan = {
            "action": "rename",
            "renames": {"/nonexistent/file.txt": "new.txt"},
            "explanation": "rename"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert "Skipped" in result.stdout or "Renamed 0" in result.stdout

    def test_execute_rename_empty(self):
        plan = {"action": "rename", "renames": {}, "explanation": "nothing"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0
        assert "No renames" in result.stdout

    # --- Run (command) action ---

    def test_execute_run_python(self, mocker):
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.return_value = type('obj', (object,), {
            'stdout': 'Hello', 'stderr': '', 'returncode': 0
        })()
        mocker.patch('alfred.which', return_value="/usr/bin/python3")

        plan = {
            "action": "run",
            "language": "python",
            "code": "print('Hello')",
            "explanation": "Print hello"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0

    def test_execute_run_bash(self, mocker):
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.return_value = type('obj', (object,), {
            'stdout': 'test', 'stderr': '', 'returncode': 0
        })()

        plan = {
            "action": "run",
            "language": "bash",
            "code": "echo test",
            "explanation": "Echo test"
        }
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 0

    def test_execute_run_no_code(self):
        plan = {"action": "run", "language": "python", "code": "", "explanation": "empty"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        assert result.exit_code == 1
        assert "No code" in result.stdout

    def test_execute_run_unknown_language(self):
        plan = {"action": "run", "language": "cobol", "code": "DISPLAY 'HI'", "explanation": "old"}
        result = runner.invoke(alfred.app, ["execute", json.dumps(plan)])
        # Should report unknown language (exit 0 since it prints error but doesn't necessarily exit 1)
        assert "Unknown language" in result.stdout or result.exit_code != 0
