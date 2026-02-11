"""Tests for utility functions in alfred.py"""

import pytest
import xml.etree.ElementTree as ET
from pathlib import Path
import alfred


class TestHumanSize:
    """Tests for _human_size() function"""
    
    def test_bytes(self):
        assert alfred._human_size(0) == "0 B"
        assert alfred._human_size(512) == "512 B"
        assert alfred._human_size(1023) == "1023 B"
    
    def test_kilobytes(self):
        assert alfred._human_size(1024) == "1.0 KB"
        assert alfred._human_size(1536) == "1.5 KB"
        assert alfred._human_size(2048) == "2.0 KB"
    
    def test_megabytes(self):
        assert alfred._human_size(1024 * 1024) == "1.0 MB"
        assert alfred._human_size(int(2.5 * 1024 * 1024)) == "2.5 MB"
    
    def test_gigabytes(self):
        assert alfred._human_size(1024 * 1024 * 1024) == "1.0 GB"
        assert alfred._human_size(int(3.7 * 1024 * 1024 * 1024)) == "3.7 GB"
    
    def test_terabytes(self):
        assert alfred._human_size(1024 * 1024 * 1024 * 1024) == "1.0 TB"
        assert alfred._human_size(int(2.3 * 1024 * 1024 * 1024 * 1024)) == "2.3 TB"


class TestCategorizeFile:
    """Tests for _categorize_file() function"""
    
    def test_images(self):
        assert alfred._categorize_file("photo.png") == "Images"
        assert alfred._categorize_file("image.jpg") == "Images"
        assert alfred._categorize_file("picture.jpeg") == "Images"
        assert alfred._categorize_file("graphic.gif") == "Images"
        assert alfred._categorize_file("icon.webp") == "Images"
        assert alfred._categorize_file("photo.heic") == "Images"
    
    def test_documents(self):
        assert alfred._categorize_file("report.pdf") == "Documents"
        assert alfred._categorize_file("letter.doc") == "Documents"
        assert alfred._categorize_file("essay.docx") == "Documents"
        assert alfred._categorize_file("note.txt") == "Documents"
        assert alfred._categorize_file("readme.md") == "Documents"
    
    def test_spreadsheets(self):
        assert alfred._categorize_file("data.csv") == "Spreadsheets"
        assert alfred._categorize_file("budget.xlsx") == "Spreadsheets"
        assert alfred._categorize_file("table.xls") == "Spreadsheets"
    
    def test_audio(self):
        assert alfred._categorize_file("song.mp3") == "Audio"
        assert alfred._categorize_file("audio.wav") == "Audio"
        assert alfred._categorize_file("music.flac") == "Audio"
        assert alfred._categorize_file("track.m4a") == "Audio"
    
    def test_video(self):
        assert alfred._categorize_file("movie.mp4") == "Video"
        assert alfred._categorize_file("clip.avi") == "Video"
        assert alfred._categorize_file("video.mkv") == "Video"
        assert alfred._categorize_file("recording.mov") == "Video"
    
    def test_code(self):
        assert alfred._categorize_file("script.py") == "Code"
        assert alfred._categorize_file("app.js") == "Code"
        assert alfred._categorize_file("page.html") == "Code"
        assert alfred._categorize_file("program.swift") == "Code"
    
    def test_data(self):
        assert alfred._categorize_file("config.json") == "Data"
        assert alfred._categorize_file("settings.xml") == "Data"
        assert alfred._categorize_file("data.yaml") == "Data"
        assert alfred._categorize_file("database.db") == "Data"
    
    def test_archives(self):
        assert alfred._categorize_file("archive.zip") == "Archives"
        assert alfred._categorize_file("backup.tar") == "Archives"
        assert alfred._categorize_file("package.dmg") == "Archives"
    
    def test_case_insensitive(self):
        assert alfred._categorize_file("IMAGE.PNG") == "Images"
        assert alfred._categorize_file("Document.PDF") == "Documents"
        assert alfred._categorize_file("AUDIO.MP3") == "Audio"
    
    def test_unknown_extension(self):
        assert alfred._categorize_file("file.xyz") == "Other"
        assert alfred._categorize_file("unknown.foo") == "Other"
    
    def test_no_extension(self):
        assert alfred._categorize_file("README") == "Other"
        assert alfred._categorize_file("Makefile") == "Other"


class TestExtractCodeBlock:
    """Tests for extract_code_block() function"""
    
    def test_python_block(self):
        response = "Here's the code:\n```python\nprint('hello')\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang == "python"
        assert code == "print('hello')"
    
    def test_bash_block(self):
        response = "Run this:\n```bash\necho 'test'\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang == "bash"
        assert code == "echo 'test'"
    
    def test_sh_block_returns_bash(self):
        response = "```sh\nls -la\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang == "bash"  # sh is normalized to bash
        assert code == "ls -la"
    
    def test_no_code_block(self):
        response = "Just plain text without code"
        lang, code = alfred.extract_code_block(response)
        assert lang is None
        assert code is None
    
    def test_malformed_block_no_closing(self):
        response = "```python\nprint('test')"
        lang, code = alfred.extract_code_block(response)
        # Current implementation is lenient - it extracts even without closing ```
        # This could be seen as a feature (graceful handling) rather than a bug
        assert lang == "python"
        assert code == "print('test')"
    
    def test_multiple_blocks_returns_first(self):
        response = "```python\nfirst()\n```\nMore text\n```bash\nsecond\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang == "python"
        assert code == "first()"
    
    def test_empty_code_block(self):
        response = "```python\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang is None  # Empty code returns None
        assert code is None
    
    def test_code_with_leading_trailing_whitespace(self):
        response = "```python\n\n  print('test')  \n\n```"
        lang, code = alfred.extract_code_block(response)
        assert lang == "python"
        assert code == "print('test')"  # strip() removes whitespace


class TestJsonToYamlSimple:
    """Tests for _json_to_yaml_simple() function"""
    
    def test_flat_dict(self):
        obj = {"name": "Alfred", "version": "0.1.0"}
        result = alfred._json_to_yaml_simple(obj)
        assert "name: Alfred" in result
        assert "version: 0.1.0" in result
    
    def test_nested_dict(self):
        obj = {"app": {"name": "Alfred", "version": "1.0"}}
        result = alfred._json_to_yaml_simple(obj)
        assert "app:" in result
        assert "  name: Alfred" in result
        assert "  version: 1.0" in result
    
    def test_list_of_primitives(self):
        obj = ["apple", "banana", "cherry"]
        result = alfred._json_to_yaml_simple(obj)
        assert "- apple" in result
        assert "- banana" in result
        assert "- cherry" in result
    
    def test_list_of_dicts(self):
        obj = [{"name": "Alice"}, {"name": "Bob"}]
        result = alfred._json_to_yaml_simple(obj)
        assert "-" in result
        # Should have nested structure
    
    def test_boolean_values(self):
        obj = {"active": True, "disabled": False}
        result = alfred._json_to_yaml_simple(obj)
        assert "active: true" in result
        assert "disabled: false" in result
    
    def test_null_value(self):
        obj = {"value": None}
        result = alfred._json_to_yaml_simple(obj)
        assert "value: null" in result
    
    def test_special_chars_quoted(self):
        obj = {"key": "value:with:colons"}
        result = alfred._json_to_yaml_simple(obj)
        # Should quote strings with colons
        # result is a list of lines, join them
        result_str = '\n'.join(result) if isinstance(result, list) else str(result)
        assert '"value:with:colons"' in result_str


class TestXmlToDict:
    """Tests for _xml_to_dict() function"""
    
    def test_simple_element(self):
        xml = "<root>value</root>"
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert result == "value"
    
    def test_element_with_attributes(self):
        xml = '<root id="1" name="test">value</root>'
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert "@attributes" in result
        assert result["@attributes"]["id"] == "1"
        assert result["@attributes"]["name"] == "test"
    
    def test_nested_elements(self):
        xml = "<root><child>value</child></root>"
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert "child" in result
        assert result["child"] == "value"
    
    def test_multiple_same_tag_creates_list(self):
        xml = "<root><item>first</item><item>second</item></root>"
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert isinstance(result["item"], list)
        assert result["item"] == ["first", "second"]
    
    def test_mixed_content(self):
        xml = '<root id="1"><child>text</child></root>'
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert "@attributes" in result
        assert "child" in result
    
    def test_element_with_text_and_children(self):
        xml = "<root>Some text<child>nested</child></root>"
        elem = ET.fromstring(xml)
        result = alfred._xml_to_dict(elem)
        assert "child" in result
        assert "#text" in result
        assert result["#text"] == "Some text"
