"""Shared pytest fixtures for Alfred CLI tests."""

import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# Add the cli directory to the path so we can import alfred
sys.path.insert(0, str(Path(__file__).parent.parent))

import alfred


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch, tmp_path):
    """Autouse fixture to prevent side effects during tests."""
    # Override config to use temp directories
    test_log = tmp_path / "test_alfred.log"
    test_app_support = tmp_path / "AppSupport"
    
    alfred._CONFIG["LOG_FILE"] = str(test_log)
    alfred._CONFIG["APP_SUPPORT_DIR"] = test_app_support
    alfred._CONFIG["AI_PROVIDER"] = "ollama"
    alfred._CONFIG["AI_MODEL"] = "test-model"
    alfred._CONFIG["OLLAMA_API_BASE"] = "http://test-ollama:11434"
    alfred._CONFIG["TEMPERATURE"] = 0.2
    
    # Create the bin directory
    (test_app_support / "bin").mkdir(parents=True, exist_ok=True)
    
    # Don't modify real PATH
    original_path = os.environ.get("PATH", "")
    yield
    os.environ["PATH"] = original_path


@pytest.fixture
def mock_ollama(mocker):
    """Mock LiteLLM completion responses."""
    def _mock_response(response_text="Success"):
        # Create a mock completion response that matches LiteLLM's structure
        mock_choice = Mock()
        mock_choice.message.content = response_text
        
        mock_resp = Mock()
        mock_resp.choices = [mock_choice]
        
        return mocker.patch('alfred.completion', return_value=mock_resp)
    
    return _mock_response


@pytest.fixture
def tmp_workspace(tmp_path):
    """Create a temporary workspace with sample files."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create sample files
    (workspace / "test.txt").write_text("Hello World", encoding="utf-8")
    (workspace / "image.png").write_bytes(b"PNG fake data")
    (workspace / "audio.mp3").write_bytes(b"MP3 fake data")
    (workspace / "document.pdf").write_bytes(b"PDF fake data")
    
    return workspace


@pytest.fixture
def mock_tools_available(mocker):
    """Mock all tools as available."""
    mocker.patch('alfred.which', return_value="/usr/bin/mock-tool")
    mocker.patch('alfred.check_command_availability', return_value=True)


@pytest.fixture
def mock_tools_missing(mocker):
    """Mock all external tools as missing (only Python/built-ins available)."""
    def _check_availability(cmd):
        # Only Python and macOS built-ins are "available"
        return cmd in ('python', 'sips', 'afconvert', 'textutil')
    
    mocker.patch('alfred.which', return_value=None)
    mocker.patch('alfred.check_command_availability', side_effect=_check_availability)


@pytest.fixture
def cli_runner():
    """Typer CLI runner for integration tests."""
    from typer.testing import CliRunner
    return CliRunner()


@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess calls to prevent actual execution."""
    mock_run = Mock()
    mock_run.return_value = Mock(
        stdout="mock output",
        stderr="",
        returncode=0
    )
    return mocker.patch('alfred.subprocess.run', mock_run)


@pytest.fixture
def sample_json_data():
    """Sample JSON data for conversion tests."""
    return [
        {"name": "Alice", "age": 30, "city": "New York"},
        {"name": "Bob", "age": 25, "city": "San Francisco"}
    ]


@pytest.fixture
def sample_csv_content():
    """Sample CSV content for conversion tests."""
    return """name,age,city
Alice,30,New York
Bob,25,San Francisco"""
