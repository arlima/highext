"""Tests for CLI interface."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from src.cli import parse_arguments, main, setup_logging


class TestParseArguments:
    """Tests for argument parsing."""
    
    def test_required_argument(self):
        """Test that input_pdf is required."""
        with patch('sys.argv', ['cli.py']):
            with pytest.raises(SystemExit):
                parse_arguments()
    
    def test_default_output(self):
        """Test default output file."""
        with patch('sys.argv', ['cli.py', 'test.pdf']):
            args = parse_arguments()
            assert args.input_pdf == 'test.pdf'
            assert args.output == 'highlights.json'
            assert not args.verbose
            assert not args.pretty
    
    def test_custom_output(self):
        """Test custom output file."""
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', 'custom.json']):
            args = parse_arguments()
            assert args.output == 'custom.json'
    
    def test_verbose_flag(self):
        """Test verbose flag."""
        with patch('sys.argv', ['cli.py', 'test.pdf', '-v']):
            args = parse_arguments()
            assert args.verbose
    
    def test_pretty_flag(self):
        """Test pretty flag."""
        with patch('sys.argv', ['cli.py', 'test.pdf', '-p']):
            args = parse_arguments()
            assert args.pretty
    
    def test_all_options(self):
        """Test all options together."""
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', 'out.json', '-v', '-p']):
            args = parse_arguments()
            assert args.input_pdf == 'test.pdf'
            assert args.output == 'out.json'
            assert args.verbose
            assert args.pretty


class TestMain:
    """Tests for main CLI function."""
    
    @patch('src.cli.extract_highlights_from_pdf')
    @patch('src.cli.validate_output_path')
    @patch('src.cli.validate_pdf_file')
    def test_successful_extraction(
        self,
        mock_validate_pdf,
        mock_validate_output,
        mock_extract,
        tmp_path
    ):
        """Test successful highlight extraction."""
        # Setup mocks
        mock_validate_pdf.return_value = (True, "")
        mock_validate_output.return_value = (True, "")
        mock_extract.return_value = {
            'source_file': 'test.pdf',
            'total_highlights': 2,
            'highlights': [
                {'page': 1, 'text': 'test', 'color': [1, 1, 0]}
            ]
        }
        
        output_file = tmp_path / "output.json"
        
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', str(output_file)]):
            exit_code = main()
        
        assert exit_code == 0
        assert output_file.exists()
        
        # Verify output file content
        with open(output_file) as f:
            data = json.load(f)
            assert data['total_highlights'] == 2
    
    @patch('src.cli.validate_pdf_file')
    def test_invalid_pdf_file(self, mock_validate_pdf):
        """Test handling of invalid PDF file."""
        mock_validate_pdf.return_value = (False, "File not found")
        
        with patch('sys.argv', ['cli.py', 'nonexistent.pdf']):
            exit_code = main()
        
        assert exit_code == 1
    
    @patch('src.cli.validate_output_path')
    @patch('src.cli.validate_pdf_file')
    def test_invalid_output_path(self, mock_validate_pdf, mock_validate_output):
        """Test handling of invalid output path."""
        mock_validate_pdf.return_value = (True, "")
        mock_validate_output.return_value = (False, "Cannot write to path")
        
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', '/invalid/path.json']):
            exit_code = main()
        
        assert exit_code == 1
    
    @patch('src.cli.extract_highlights_from_pdf')
    @patch('src.cli.validate_output_path')
    @patch('src.cli.validate_pdf_file')
    def test_no_highlights_found(
        self,
        mock_validate_pdf,
        mock_validate_output,
        mock_extract,
        tmp_path
    ):
        """Test handling when no highlights are found."""
        mock_validate_pdf.return_value = (True, "")
        mock_validate_output.return_value = (True, "")
        mock_extract.return_value = {
            'source_file': 'test.pdf',
            'total_highlights': 0,
            'highlights': []
        }
        
        output_file = tmp_path / "empty.json"
        
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', str(output_file)]):
            exit_code = main()
        
        # Should still succeed, just with warning
        assert exit_code == 0
        assert output_file.exists()
    
    @patch('src.cli.extract_highlights_from_pdf')
    @patch('src.cli.validate_output_path')
    @patch('src.cli.validate_pdf_file')
    def test_extraction_error(
        self,
        mock_validate_pdf,
        mock_validate_output,
        mock_extract
    ):
        """Test handling of extraction errors."""
        mock_validate_pdf.return_value = (True, "")
        mock_validate_output.return_value = (True, "")
        mock_extract.side_effect = Exception("Extraction failed")
        
        with patch('sys.argv', ['cli.py', 'test.pdf']):
            exit_code = main()
        
        assert exit_code == 1
    
    @patch('src.cli.extract_highlights_from_pdf')
    @patch('src.cli.validate_output_path')
    @patch('src.cli.validate_pdf_file')
    def test_pretty_output(
        self,
        mock_validate_pdf,
        mock_validate_output,
        mock_extract,
        tmp_path
    ):
        """Test pretty-printed output."""
        mock_validate_pdf.return_value = (True, "")
        mock_validate_output.return_value = (True, "")
        mock_extract.return_value = {
            'source_file': 'test.pdf',
            'total_highlights': 1,
            'highlights': []
        }
        
        output_file = tmp_path / "pretty.json"
        
        with patch('sys.argv', ['cli.py', 'test.pdf', '-o', str(output_file), '-p']):
            exit_code = main()
        
        assert exit_code == 0
        
        # Check that output is pretty-printed
        content = output_file.read_text()
        assert '\n' in content
        assert '  ' in content  # Indentation


class TestSetupLogging:
    """Tests for logging setup."""
    
    def test_normal_logging(self):
        """Test normal logging level."""
        setup_logging(verbose=False)
        # Just verify it doesn't raise an exception
    
    def test_verbose_logging(self):
        """Test verbose logging level."""
        setup_logging(verbose=True)
        # Just verify it doesn't raise an exception
