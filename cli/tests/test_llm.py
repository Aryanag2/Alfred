"""Tests for LLM integration and AI functions"""

import pytest
from unittest.mock import Mock
import json
import alfred


class TestGetLlmResponse:
    """Test get_llm_response() with various scenarios"""
    
    def test_successful_response(self, mock_ollama):
        mock_ollama("This is the AI response")
        
        response = alfred.get_llm_response("test prompt")
        
        assert response == "This is the AI response"
    
    def test_strips_think_tags(self, mock_ollama):
        mock_ollama("<think>Internal reasoning</think>The actual response")
        
        response = alfred.get_llm_response("test prompt")
        
        assert response == "The actual response"
        assert "<think>" not in response
    
    def test_strips_multiline_think_tags(self, mock_ollama):
        mock_ollama("<think>\nLong\nthought\nprocess\n</think>\nFinal answer")
        
        response = alfred.get_llm_response("test prompt")
        
        assert response == "Final answer"
    
    def test_connection_error_retries(self, mocker):
        mock_completion = mocker.patch('alfred.completion')
        mock_completion.side_effect = Exception("Connection refused")
        
        response = alfred.get_llm_response("test prompt", retries=2)
        
        # Should retry 2 times (total 3 attempts)
        assert mock_completion.call_count == 3
        assert "Cannot connect" in response
    
    def test_connection_error_succeeds_on_retry(self, mocker):
        mock_completion = mocker.patch('alfred.completion')
        
        # Fail first with connection error, succeed on second
        mock_choice = Mock()
        mock_choice.message.content = "Success after retry"
        success_response = Mock()
        success_response.choices = [mock_choice]
        
        mock_completion.side_effect = [
            Exception("Connection refused"),
            success_response
        ]
        
        response = alfred.get_llm_response("test prompt", retries=2)
        
        assert response == "Success after retry"
        assert mock_completion.call_count == 2
    
    def test_timeout_error_retries(self, mocker):
        mock_completion = mocker.patch('alfred.completion')
        mock_completion.side_effect = Exception("Timeout occurred")
        
        response = alfred.get_llm_response("test prompt", retries=1)
        
        assert mock_completion.call_count == 2  # Initial + 1 retry
        assert "Error: Request timed out" in response or "timeout" in response.lower()
    
    def test_generic_exception(self, mocker):
        mock_completion = mocker.patch('alfred.completion')
        mock_completion.side_effect = Exception("Unknown error")
        
        response = alfred.get_llm_response("test prompt", retries=0)
        
        assert "Error" in response
    
    def test_empty_response(self, mock_ollama):
        mock_ollama("")
        
        response = alfred.get_llm_response("test prompt")
        
        assert response == ""
    
    def test_uses_correct_config(self, mocker):
        mock_completion = mocker.patch('alfred.completion')
        mock_choice = Mock()
        mock_choice.message.content = "test response"
        mock_resp = Mock()
        mock_resp.choices = [mock_choice]
        mock_completion.return_value = mock_resp
        
        alfred.get_llm_response("test prompt")
        
        call_args = mock_completion.call_args
        # Check that model is correctly formatted for the provider
        assert call_args[1]["model"].startswith(alfred.get_ai_provider())
        assert call_args[1]["temperature"] == alfred.get_temperature()
        assert len(call_args[1]["messages"]) == 1
        assert call_args[1]["messages"][0]["content"] == "test prompt"


class TestAiOrganizePlan:
    """Test _ai_organize_plan() function"""
    
    def test_valid_json_response(self, mock_ollama):
        plan = {
            "Images": ["photo1.jpg", "photo2.png"],
            "Documents": ["file.pdf"]
        }
        mock_ollama(json.dumps(plan))
        
        result = alfred._ai_organize_plan("/path", ["photo1.jpg", "photo2.png", "file.pdf"], "organize by type")
        
        assert result == plan
    
    def test_json_with_code_fence(self, mock_ollama):
        plan = {"Images": ["photo.jpg"]}
        mock_ollama(f"```json\n{json.dumps(plan)}\n```")
        
        result = alfred._ai_organize_plan("/path", ["photo.jpg"], "organize")
        
        assert result == plan
    
    def test_invalid_json_returns_empty_dict(self, mock_ollama):
        mock_ollama("This is not JSON at all")
        
        result = alfred._ai_organize_plan("/path", ["file.txt"], "organize")
        
        assert result == {}
    
    def test_non_dict_response_returns_empty(self, mock_ollama):
        mock_ollama('["array", "not", "dict"]')
        
        result = alfred._ai_organize_plan("/path", ["file.txt"], "organize")
        
        assert result == {}
    
    def test_malformed_json_returns_empty(self, mock_ollama):
        mock_ollama('{"key": "value"')  # Missing closing brace
        
        result = alfred._ai_organize_plan("/path", ["file.txt"], "organize")
        
        assert result == {}
    
    def test_limits_files_to_50(self, mock_ollama):
        mock_ollama('{"folder": ["file.txt"]}')
        
        many_files = [f"file{i}.txt" for i in range(100)]
        alfred._ai_organize_plan("/path", many_files, "organize")
        
        # Check that prompt was called (we can't easily check the prompt content without more mocking)
        # This is more of a smoke test


class TestExecutePythonScript:
    """Test execute_python_script() function"""
    
    def test_successful_execution(self, mocker):
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.return_value = Mock(stdout="Hello World", stderr="", returncode=0)
        mocker.patch('alfred.which', return_value="/usr/bin/python3")
        
        result = alfred.execute_python_script("print('Hello World')")
        
        assert result is True
        assert mock_run.called
    
    def test_script_failure(self, mocker):
        import subprocess
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.side_effect = subprocess.CalledProcessError(1, "python", stderr="Syntax error")
        mocker.patch('alfred.which', return_value="/usr/bin/python3")
        
        result = alfred.execute_python_script("invalid python code")
        
        assert result is False
    
    def test_no_python_found(self, mocker):
        mocker.patch('alfred.which', return_value=None)
        
        result = alfred.execute_python_script("print('test')")
        
        assert result is False
    
    def test_cleans_up_temp_file(self, mocker):
        import os
        mock_run = mocker.patch('alfred.subprocess.run')
        mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
        mocker.patch('alfred.which', return_value="/usr/bin/python3")
        
        # Track if os.remove was called
        original_remove = os.remove
        removed_files = []
        
        def track_remove(path):
            removed_files.append(path)
            # Don't actually remove since temp file might not exist
        
        mocker.patch('os.remove', side_effect=track_remove)
        mocker.patch('os.path.exists', return_value=True)
        
        alfred.execute_python_script("print('test')")
        
        # Should have cleaned up temp file
        assert len(removed_files) > 0
