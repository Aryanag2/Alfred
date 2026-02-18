"""Tests for tool resolution and conversion engine"""

import pytest
from pathlib import Path
import alfred


class TestToolSupportsTarget:
    """Test _tool_supports_target() format capability checking"""
    
    def test_python_supports_all(self):
        # Python converter is assumed to handle its own formats
        assert alfred._tool_supports_target("python", "csv")
        assert alfred._tool_supports_target("python", "json")
    
    def test_sips_supported_formats(self):
        assert alfred._tool_supports_target("sips", "jpeg")
        assert alfred._tool_supports_target("sips", "png")
        assert alfred._tool_supports_target("sips", "tiff")
        assert alfred._tool_supports_target("sips", "gif")
        assert alfred._tool_supports_target("sips", "heic")
    
    def test_sips_unsupported_formats(self):
        assert not alfred._tool_supports_target("sips", "webp")
        assert not alfred._tool_supports_target("sips", "mp4")
    
    def test_afconvert_supported_formats(self):
        assert alfred._tool_supports_target("afconvert", "aac")
        assert alfred._tool_supports_target("afconvert", "m4a")
        assert alfred._tool_supports_target("afconvert", "wav")
        assert alfred._tool_supports_target("afconvert", "aiff")
    
    def test_afconvert_unsupported_formats(self):
        assert not alfred._tool_supports_target("afconvert", "mp3")
        assert not alfred._tool_supports_target("afconvert", "flac")
    
    def test_textutil_supported_formats(self):
        assert alfred._tool_supports_target("textutil", "txt")
        assert alfred._tool_supports_target("textutil", "html")
        assert alfred._tool_supports_target("textutil", "rtf")
        assert alfred._tool_supports_target("textutil", "docx")
    
    def test_textutil_cannot_output_pdf(self):
        # textutil cannot create PDFs
        assert not alfred._tool_supports_target("textutil", "pdf")
    
    def test_pandoc_supported_formats(self):
        assert alfred._tool_supports_target("pandoc", "html")
        assert alfred._tool_supports_target("pandoc", "pdf")
        assert alfred._tool_supports_target("pandoc", "docx")
        assert alfred._tool_supports_target("pandoc", "md")
        assert alfred._tool_supports_target("pandoc", "epub")
    
    def test_ffmpeg_supported_formats(self):
        assert alfred._tool_supports_target("ffmpeg", "mp3")
        assert alfred._tool_supports_target("ffmpeg", "mp4")
        assert alfred._tool_supports_target("ffmpeg", "wav")
        assert alfred._tool_supports_target("ffmpeg", "avi")
        assert alfred._tool_supports_target("ffmpeg", "gif")
    
    def test_magick_supported_formats(self):
        assert alfred._tool_supports_target("magick", "jpg")
        assert alfred._tool_supports_target("magick", "png")
        assert alfred._tool_supports_target("magick", "webp")
        assert alfred._tool_supports_target("magick", "gif")
    
    def test_unknown_tool(self):
        assert not alfred._tool_supports_target("unknown_tool", "pdf")
    
    def test_case_insensitive(self):
        assert alfred._tool_supports_target("sips", "PNG")
        assert alfred._tool_supports_target("sips", "JPEG")


class TestResolveToolchecks:
    """Test _resolve_tool() availability checking"""
    
    def test_python_always_available(self):
        tool = alfred._resolve_tool(["python"])
        assert tool == "python"
    
    def test_macos_builtins_always_available(self):
        assert alfred._resolve_tool(["sips"]) == "sips"
        assert alfred._resolve_tool(["afconvert"]) == "afconvert"
        assert alfred._resolve_tool(["textutil"]) == "textutil"
    
    def test_ffmpeg_when_available(self, mocker):
        mocker.patch('alfred.check_command_availability', return_value=True)
        tool = alfred._resolve_tool(["ffmpeg"])
        assert tool == "ffmpeg"
    
    def test_ffmpeg_when_missing(self, mocker):
        mocker.patch('alfred.check_command_availability', return_value=False)
        tool = alfred._resolve_tool(["ffmpeg"])
        assert tool is None
    
    def test_priority_first_available_wins(self, mocker):
        # Mock: sips available, ffmpeg not
        def check_avail(cmd):
            return cmd == "sips"
        mocker.patch('alfred.check_command_availability', side_effect=check_avail)
        tool = alfred._resolve_tool(["sips", "ffmpeg"])
        assert tool == "sips"
    
    def test_priority_fallback_to_second(self, mocker):
        # Mock: magick not available, sips available
        def check_avail(cmd):
            return cmd in ("sips", "afconvert", "textutil")  # macOS builtins
        mocker.patch('alfred.check_command_availability', side_effect=check_avail)
        tool = alfred._resolve_tool(["magick", "sips"])
        assert tool == "sips"
    
    def test_all_unavailable(self, mocker):
        mocker.patch('alfred.check_command_availability', return_value=False)
        tool = alfred._resolve_tool(["ffmpeg", "pandoc", "magick"])
        assert tool is None
    
    def test_empty_list(self):
        tool = alfred._resolve_tool([])
        assert tool is None


class TestCheckCommandAvailability:
    """Test check_command_availability() function"""
    
    def test_tool_in_local_bin(self, tmp_path, mocker):
        # Create a fake local bin dir with an executable
        local_bin = tmp_path / "bin"
        local_bin.mkdir()
        fake_tool = local_bin / "ffmpeg"
        fake_tool.write_text("#!/bin/sh\necho fake")
        fake_tool.chmod(0o755)
        
        # Mock the config to return our test dir
        mocker.patch.object(alfred, 'get_local_bin_dir', return_value=local_bin)
        
        assert alfred.check_command_availability("ffmpeg") is True
    
    def test_tool_in_path(self, tmp_path, mocker):
        # Mock: not in local bin, but which() finds it
        mocker.patch.object(alfred, 'get_local_bin_dir', return_value=tmp_path / "empty")
        mocker.patch('alfred.which', return_value="/usr/bin/ls")
        
        assert alfred.check_command_availability("ls") is True
    
    def test_tool_not_found(self, tmp_path, mocker):
        mocker.patch.object(alfred, 'get_local_bin_dir', return_value=tmp_path / "empty")
        mocker.patch('alfred.which', return_value=None)
        
        assert alfred.check_command_availability("nonexistent") is False


class TestConversionMap:
    """Test CONVERSION_MAP completeness"""
    
    def test_common_image_conversions(self):
        assert ".png->.jpg" in alfred.CONVERSION_MAP
        assert ".jpg->.png" in alfred.CONVERSION_MAP
        assert ".png->.webp" in alfred.CONVERSION_MAP
        assert ".webp->.png" in alfred.CONVERSION_MAP
    
    def test_audio_conversions(self):
        assert ".wav->.aac" in alfred.CONVERSION_MAP
        assert ".wav->.m4a" in alfred.CONVERSION_MAP
        assert ".mp3->.wav" in alfred.CONVERSION_MAP
        assert ".wav->.mp3" in alfred.CONVERSION_MAP
    
    def test_video_conversions(self):
        assert ".mp4->.mp3" in alfred.CONVERSION_MAP
        assert ".mp4->.wav" in alfred.CONVERSION_MAP
    
    def test_document_conversions(self):
        assert ".txt->.html" in alfred.CONVERSION_MAP
        assert ".docx->.pdf" in alfred.CONVERSION_MAP
        assert ".md->.html" in alfred.CONVERSION_MAP
        assert ".md->.pdf" in alfred.CONVERSION_MAP
    
    def test_data_conversions(self):
        assert ".json->.csv" in alfred.CONVERSION_MAP
        assert ".csv->.json" in alfred.CONVERSION_MAP
    
    def test_all_entries_have_valid_tools(self):
        valid_tools = {
            "python", "sips", "afconvert", "textutil", "pandoc", "ffmpeg", "magick",
            # Bundled Python library tools
            "pillow", "pydub", "py_docx", "py_markdown", "py_pdf",
            "py_yaml", "py_xlsx", "py_toml", "py_epub",
        }
        for key, tool_list in alfred.CONVERSION_MAP.items():
            assert isinstance(tool_list, list), f"{key} should map to a list"
            assert len(tool_list) > 0, f"{key} has empty tool list"
            for tool in tool_list:
                assert tool in valid_tools, f"Unknown tool {tool} in {key}"


class TestExtensionCategories:
    """Test EXTENSION_CATEGORIES structure"""
    
    def test_all_categories_exist(self):
        expected = ["Images", "Documents", "Spreadsheets", "Audio", "Video", 
                   "Archives", "Code", "Data", "Presentations", "Design"]
        for cat in expected:
            assert cat in alfred.EXTENSION_CATEGORIES
    
    def test_extensions_are_lowercase_with_dot(self):
        for category, exts in alfred.EXTENSION_CATEGORIES.items():
            for ext in exts:
                assert ext.startswith("."), f"{category}: {ext} should start with dot"
                assert ext == ext.lower(), f"{category}: {ext} should be lowercase"
    
    def test_no_duplicate_extensions(self):
        all_exts = []
        for exts in alfred.EXTENSION_CATEGORIES.values():
            all_exts.extend(exts)
        # Check for duplicates
        assert len(all_exts) == len(set(all_exts)), "Found duplicate extensions across categories"
