"""Tests for utility functions."""

import json
import tempfile
from pathlib import Path

import pytest

from src.utils import (
    rgb_to_color_name,
    format_json_output,
    validate_pdf_file,
    validate_output_path
)


class TestRgbToColorName:
    """Tests for RGB to color name conversion."""
    
    def test_yellow(self):
        assert rgb_to_color_name((1.0, 1.0, 0.0)) == "Yellow"
    
    def test_red(self):
        assert rgb_to_color_name((1.0, 0.0, 0.0)) == "Red"
    
    def test_green(self):
        assert rgb_to_color_name((0.0, 1.0, 0.0)) == "Green"
    
    def test_blue(self):
        assert rgb_to_color_name((0.0, 0.0, 1.0)) == "Blue"
    
    def test_orange(self):
        assert rgb_to_color_name((1.0, 0.5, 0.0)) == "Orange"
    
    def test_unknown_color_reddish(self):
        result = rgb_to_color_name((0.8, 0.2, 0.1))
        assert "Red" in result
    
    def test_unknown_color_greenish(self):
        result = rgb_to_color_name((0.2, 0.8, 0.1))
        assert "Green" in result
    
    def test_unknown_color_blueish(self):
        result = rgb_to_color_name((0.1, 0.2, 0.8))
        assert "Blue" in result


class TestFormatJsonOutput:
    """Tests for JSON formatting."""
    
    def test_compact_format(self):
        data = {"key": "value", "number": 42}
        result = format_json_output(data, pretty=False)
        assert "\n" not in result or result.count("\n") <= 1
        parsed = json.loads(result)
        assert parsed == data
    
    def test_pretty_format(self):
        data = {"key": "value", "number": 42}
        result = format_json_output(data, pretty=True)
        assert "\n" in result
        assert "  " in result  # Check for indentation
        parsed = json.loads(result)
        assert parsed == data
    
    def test_unicode_characters(self):
        data = {"text": "Hello 世界 🌍"}
        result = format_json_output(data, pretty=False)
        assert "世界" in result
        assert "🌍" in result
        parsed = json.loads(result)
        assert parsed == data


class TestValidatePdfFile:
    """Tests for PDF file validation."""
    
    def test_nonexistent_file(self):
        is_valid, error_msg = validate_pdf_file("/nonexistent/file.pdf")
        assert not is_valid
        assert "not found" in error_msg.lower()
    
    def test_non_pdf_extension(self, tmp_path):
        # Create a temporary non-PDF file
        temp_file = tmp_path / "test.txt"
        temp_file.write_text("not a pdf")
        
        is_valid, error_msg = validate_pdf_file(str(temp_file))
        assert not is_valid
        assert "not a pdf" in error_msg.lower()
    
    def test_directory_instead_of_file(self, tmp_path):
        is_valid, error_msg = validate_pdf_file(str(tmp_path))
        assert not is_valid
        assert "not a file" in error_msg.lower()
    
    def test_valid_pdf_file(self, tmp_path):
        # Create a temporary PDF file
        temp_file = tmp_path / "test.pdf"
        temp_file.write_text("fake pdf content")
        
        is_valid, error_msg = validate_pdf_file(str(temp_file))
        assert is_valid
        assert error_msg == ""


class TestValidateOutputPath:
    """Tests for output path validation."""
    
    def test_valid_output_path(self, tmp_path):
        output_file = tmp_path / "output.json"
        is_valid, error_msg = validate_output_path(str(output_file))
        assert is_valid
        assert error_msg == ""
    
    def test_create_parent_directory(self, tmp_path):
        output_file = tmp_path / "subdir" / "output.json"
        is_valid, error_msg = validate_output_path(str(output_file))
        assert is_valid
        assert error_msg == ""
        assert output_file.parent.exists()
    
    def test_existing_writable_file(self, tmp_path):
        output_file = tmp_path / "existing.json"
        output_file.write_text("old content")
        
        is_valid, error_msg = validate_output_path(str(output_file))
        assert is_valid
        assert error_msg == ""
