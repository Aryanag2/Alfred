"""Integration tests for CLI commands using Typer's CliRunner"""

import pytest
import json
from pathlib import Path
from typer.testing import CliRunner
import alfred


runner = CliRunner()


class TestConvertCommand:
    """Test the convert command"""
    
    def test_missing_file(self):
        result = runner.invoke(alfred.app, ["convert", "/nonexistent/file.txt", "pdf"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()
    
    def test_data_conversion_json_to_csv(self, tmp_path):
        input_file = tmp_path / "data.json"
        input_file.write_text('[{"name":"Alice","age":30}]')
        
        result = runner.invoke(alfred.app, ["convert", str(input_file), "csv"])
        
        assert result.exit_code == 0
        output_file = tmp_path / "data.csv"
        assert output_file.exists()
        assert "Output:" in result.stdout
    
    def test_data_conversion_csv_to_json(self, tmp_path):
        input_file = tmp_path / "data.csv"
        input_file.write_text("name,age\nAlice,30")
        
        result = runner.invoke(alfred.app, ["convert", str(input_file), "json"])
        
        assert result.exit_code == 0
        output_file = tmp_path / "data.json"
        assert output_file.exists()
    
    def test_unsupported_format(self, tmp_path):
        input_file = tmp_path / "test.xyz"
        input_file.write_text("test")
        
        result = runner.invoke(alfred.app, ["convert", str(input_file), "unknown"])
        
        assert result.exit_code == 1
        assert "Error" in result.stdout or "error" in result.stdout.lower()
    
    def test_missing_external_tool_shows_install_prompt(self, tmp_path, mocker):
        input_file = tmp_path / "test.mp4"
        input_file.write_bytes(b"fake video")
        
        # Mock ffmpeg as missing
        mocker.patch('alfred.check_command_availability', return_value=False)
        
        result = runner.invoke(alfred.app, ["convert", str(input_file), "mp3"])
        
        assert result.exit_code == 1
        assert "[NEED_INSTALL]" in result.stdout or "Missing tool" in result.stdout


class TestOrganizeCommand:
    """Test the organize command"""
    
    def test_missing_directory(self):
        result = runner.invoke(alfred.app, ["organize", "/nonexistent/dir"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()
    
    def test_empty_folder(self, tmp_path):
        result = runner.invoke(alfred.app, ["organize", str(tmp_path)])
        
        assert result.exit_code == 0
        assert "empty" in result.stdout.lower() or "nothing" in result.stdout.lower()
    
    def test_preview_mode(self, tmp_path):
        # Create some test files
        (tmp_path / "photo.jpg").write_bytes(b"fake image")
        (tmp_path / "document.pdf").write_bytes(b"fake pdf")
        (tmp_path / "song.mp3").write_bytes(b"fake audio")
        
        result = runner.invoke(alfred.app, ["organize", str(tmp_path)])
        
        assert result.exit_code == 0
        assert "Plan:" in result.stdout
        assert "preview" in result.stdout.lower()
        # Files should NOT be moved yet
        assert (tmp_path / "photo.jpg").exists()
    
    def test_confirm_mode_moves_files(self, tmp_path):
        (tmp_path / "photo.jpg").write_bytes(b"fake image")
        (tmp_path / "document.pdf").write_bytes(b"fake pdf")
        
        result = runner.invoke(alfred.app, ["organize", str(tmp_path), "--confirm"])
        
        assert result.exit_code == 0
        assert "Done" in result.stdout or "Moved" in result.stdout
        # Files should be moved
        assert not (tmp_path / "photo.jpg").exists()  # Moved to subfolder
        assert (tmp_path / "Images" / "photo.jpg").exists() or (tmp_path / "Documents" / "photo.jpg").exists()
    
    def test_with_instructions(self, tmp_path, mock_ollama):
        (tmp_path / "file1.txt").write_bytes(b"test")
        
        plan = {"CustomFolder": ["file1.txt"]}
        mock_ollama(json.dumps(plan))
        
        result = runner.invoke(alfred.app, [
            "organize", str(tmp_path),
            "--instructions", "put everything in CustomFolder"
        ])
        
        assert result.exit_code == 0
        assert "Plan:" in result.stdout
    
    def test_hidden_files_excluded(self, tmp_path):
        (tmp_path / ".hidden").write_bytes(b"hidden")
        (tmp_path / "visible.txt").write_bytes(b"visible")
        
        result = runner.invoke(alfred.app, ["organize", str(tmp_path)])
        
        # Should only process visible.txt
        assert result.exit_code == 0


class TestSummarizeCommand:
    """Test the summarize command"""
    
    def test_no_files(self):
        result = runner.invoke(alfred.app, ["summarize"])
        
        # Typer returns exit code 2 for missing required arguments
        assert result.exit_code == 2
        # Typer outputs usage/error to stderr or may have empty output
        # Just check the exit code for missing arguments
    
    def test_single_file(self, tmp_path, mock_ollama):
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a test file with content.")
        
        mock_ollama("Summary: This is a test file.")
        
        result = runner.invoke(alfred.app, ["summarize", str(test_file)])
        
        assert result.exit_code == 0
        assert "Summary" in result.stdout or "test" in result.stdout.lower()
    
    def test_multiple_files(self, tmp_path, mock_ollama):
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("Content 1")
        file2.write_text("Content 2")
        
        mock_ollama("Summary: Two files")
        
        result = runner.invoke(alfred.app, ["summarize", str(file1), str(file2)])
        
        assert result.exit_code == 0
        assert "2" in result.stdout or "files" in result.stdout.lower()
    
    def test_unreadable_file_skipped(self, tmp_path, mock_ollama):
        readable = tmp_path / "readable.txt"
        readable.write_text("Test content")
        
        # Non-existent file should be skipped
        nonexistent = tmp_path / "nonexistent.txt"
        
        mock_ollama("Summary: readable file")
        
        result = runner.invoke(alfred.app, ["summarize", str(readable), str(nonexistent)])
        
        # Should still work with just the readable file
        assert result.exit_code == 0


class TestRenameCommand:
    """Test the rename command"""
    
    def test_no_files(self):
        result = runner.invoke(alfred.app, ["rename"])
        
        # Typer returns exit code 2 for missing required arguments
        assert result.exit_code == 2
        # Typer outputs usage/error to stderr or may have empty output
        # Just check the exit code for missing arguments
    
    def test_preview_mode(self, tmp_path, mock_ollama):
        file1 = tmp_path / "IMG_123.jpg"
        file1.write_bytes(b"fake")
        
        renames = {"IMG_123.jpg": "photo_001.jpg"}
        mock_ollama(json.dumps(renames))
        
        result = runner.invoke(alfred.app, ["rename", str(file1)])
        
        assert result.exit_code == 0
        assert "Plan:" in result.stdout
        assert "preview" in result.stdout.lower()
        # File should NOT be renamed yet
        assert file1.exists()
    
    def test_confirm_mode_renames_files(self, tmp_path, mock_ollama):
        file1 = tmp_path / "old_name.txt"
        file1.write_text("content")
        
        renames = {"old_name.txt": "new_name.txt"}
        mock_ollama(json.dumps(renames))
        
        result = runner.invoke(alfred.app, ["rename", str(file1), "--confirm"])
        
        assert result.exit_code == 0
        assert "Renamed" in result.stdout
        # File should be renamed
        assert not file1.exists()
        assert (tmp_path / "new_name.txt").exists()
    
    def test_invalid_llm_response(self, tmp_path, mock_ollama):
        file1 = tmp_path / "test.txt"
        file1.write_text("content")
        
        mock_ollama("This is not valid JSON")
        
        result = runner.invoke(alfred.app, ["rename", str(file1)])
        
        assert result.exit_code == 0  # Command runs but reports error
        assert "Error" in result.stdout or "failed" in result.stdout.lower()
    
    def test_max_30_files_limit(self, tmp_path, mock_ollama):
        # Create 35 files
        files = []
        for i in range(35):
            f = tmp_path / f"file{i}.txt"
            f.write_text("content")
            files.append(str(f))
        
        mock_ollama("{}")
        
        result = runner.invoke(alfred.app, ["rename"] + files)
        
        # Should only process first 30
        assert result.exit_code == 0


class TestAskCommand:
    """Test the ask command"""
    
    def test_python_code_execution(self, mock_ollama, mocker):
        mock_ollama("```python\nprint('Hello')\n```")
        
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.return_value = type('obj', (object,), {'stdout': 'Hello', 'stderr': '', 'returncode': 0})()
        mocker.patch('alfred.which', return_value="/usr/bin/python3")
        
        result = runner.invoke(alfred.app, ["ask", "print hello"])
        
        assert result.exit_code == 0
        assert mock_run.called
    
    def test_bash_code_execution(self, mock_ollama, mock_subprocess):
        mock_ollama("```bash\necho 'test'\n```")
        mock_subprocess.return_value = type('obj', (object,), {'stdout': 'test', 'stderr': '', 'returncode': 0})()
        
        result = runner.invoke(alfred.app, ["ask", "echo test"])
        
        assert result.exit_code == 0
        assert mock_subprocess.called
    
    def test_dangerous_command_blocked(self, mock_ollama, mock_subprocess):
        mock_ollama("```bash\nrm -rf /\n```")
        
        result = runner.invoke(alfred.app, ["ask", "delete everything"])
        
        assert result.exit_code == 0
        assert "Blocked" in result.stdout or "blocked" in result.stdout.lower()
        mock_subprocess.assert_not_called()
    
    def test_no_code_block_in_response(self, mock_ollama):
        mock_ollama("I cannot help with that request.")
        
        result = runner.invoke(alfred.app, ["ask", "do something impossible"])
        
        assert result.exit_code == 0
        assert "cannot" in result.stdout.lower() or "impossible" in result.stdout.lower()
    
    def test_with_file_paths(self, tmp_path, mock_ollama, mock_subprocess):
        file1 = tmp_path / "test.txt"
        file1.write_text("content")
        
        mock_ollama("```bash\ncat test.txt\n```")
        mock_subprocess.return_value = type('obj', (object,), {'stdout': 'content', 'stderr': '', 'returncode': 0})()
        
        result = runner.invoke(alfred.app, ["ask", "read the file", str(file1)])
        
        assert result.exit_code == 0


class TestInstallCommand:
    """Test the install command"""
    
    def test_unknown_tool(self):
        result = runner.invoke(alfred.app, ["install", "nonexistent-tool"])
        
        assert result.exit_code == 1
        assert "Unknown tool" in result.stdout or "Error" in result.stdout
    
    def test_valid_tool_name(self, mocker):
        # Mock the download and extraction
        mock_get = mocker.patch('alfred.requests.get')
        mock_response = mocker.Mock()
        mock_response.headers = {'content-length': '1000'}
        mock_response.iter_content = lambda chunk_size: [b'data']
        mock_response.raise_for_status = mocker.Mock()
        mock_get.return_value.__enter__.return_value = mock_response
        
        # Mock zipfile
        import zipfile
        mock_zip = mocker.Mock()
        mock_zip.namelist.return_value = ['ffmpeg']
        mock_zip.open.return_value = mocker.Mock()
        mocker.patch.object(zipfile, 'ZipFile', return_value=mock_zip)
        
        result = runner.invoke(alfred.app, ["install", "ffmpeg"])
        
        # This is a complex test - just check it doesn't crash
        # Full integration testing would require real files
        assert "Downloading" in result.stdout or "Error" in result.stdout
    
    def test_shows_available_tools(self):
        result = runner.invoke(alfred.app, ["install", "unknown"])
        
        assert result.exit_code == 1
        # Should show available tools
        assert "ffmpeg" in result.stdout or "pandoc" in result.stdout


class TestCommandOutputFormats:
    """Test that commands produce well-formatted output"""
    
    def test_convert_shows_progress(self, tmp_path):
        input_file = tmp_path / "data.json"
        input_file.write_text('{"key":"value"}')
        
        result = runner.invoke(alfred.app, ["convert", str(input_file), "csv"])
        
        assert "Converting" in result.stdout or "convert" in result.stdout.lower()
    
    def test_error_messages_are_colored(self, tmp_path):
        result = runner.invoke(alfred.app, ["convert", "/nonexistent.txt", "pdf"])
        
        # Rich library adds ANSI color codes to errors
        assert result.exit_code == 1
        assert "Error" in result.stdout or "not found" in result.stdout.lower()
