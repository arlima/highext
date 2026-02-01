"""Tests for PDF extraction functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.extractor import HighlightExtractor, extract_highlights_from_pdf


class TestHighlightExtractor:
    """Tests for HighlightExtractor class."""
    
    @patch('src.extractor.fitz.open')
    def test_context_manager(self, mock_fitz_open):
        """Test that extractor works as a context manager."""
        mock_doc = Mock()
        mock_fitz_open.return_value = mock_doc
        
        with HighlightExtractor("test.pdf") as extractor:
            assert extractor.doc == mock_doc
        
        mock_doc.close.assert_called_once()
    
    @patch('src.extractor.fitz.open')
    def test_extract_highlights_empty_pdf(self, mock_fitz_open):
        """Test extraction from PDF with no highlights."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        mock_page = Mock()
        mock_page.annots.return_value = None
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        with HighlightExtractor("test.pdf") as extractor:
            result = extractor.extract_highlights()
        
        assert result['total_highlights'] == 0
        assert result['highlights'] == []
        assert result['total_pages'] == 1
    
    @patch('src.extractor.fitz.open')
    def test_extract_highlights_with_data(self, mock_fitz_open):
        """Test extraction from PDF with highlights."""
        # Create mock document
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        
        # Create mock annotation (highlight)
        mock_annot = Mock()
        mock_annot.type = (8, "Highlight")  # Type 8 is highlight
        mock_annot.colors = {"stroke": [1.0, 1.0, 0.0]}
        mock_annot.rect = Mock(x0=100, y0=200, x1=300, y1=220)
        mock_annot.vertices = []
        mock_annot.info = {}
        
        # Create mock page
        mock_page = Mock()
        mock_page.annots.return_value = [mock_annot]
        mock_page.get_text.return_value = "Highlighted text"
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        with HighlightExtractor("test.pdf") as extractor:
            result = extractor.extract_highlights()
    
        assert result['total_highlights'] == 1
        assert len(result['highlights']) == 1
    
        highlight = result['highlights'][0]
        assert highlight['page'] == 1
        assert highlight['text'] == "Highlighted text"
        assert highlight['color'] == [1.0, 1.0, 0.0]
        assert highlight['color_name'] == "Yellow"
    
    @patch('src.extractor.fitz.open')
    def test_extract_highlights_skips_non_highlights(self, mock_fitz_open):
        """Test that non-highlight annotations are skipped."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        
        # Create mock non-highlight annotation
        mock_annot = Mock()
        mock_annot.type = (1, "Text")  # Not a highlight
        
        mock_page = Mock()
        mock_page.annots.return_value = [mock_annot]
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        with HighlightExtractor("test.pdf") as extractor:
            result = extractor.extract_highlights()
        
        assert result['total_highlights'] == 0
        assert result['highlights'] == []
    
    @patch('src.extractor.fitz.open')
    def test_extract_highlights_handles_errors(self, mock_fitz_open):
        """Test that errors in individual annotations don't stop extraction."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 1
        
        # Create two annotations: one that fails, one that succeeds
        mock_bad_annot = Mock()
        mock_bad_annot.type = (8, "Highlight")
        mock_bad_annot.colors = {"stroke": [1.0, 1.0, 0.0]}
        mock_bad_annot.rect = Mock(x0=100, y0=200, x1=300, y1=220)
        mock_bad_annot.vertices = []
        mock_bad_annot.info = {}
        
        mock_good_annot = Mock()
        mock_good_annot.type = (8, "Highlight")
        mock_good_annot.colors = {"stroke": [0.0, 1.0, 0.0]}
        mock_good_annot.rect = Mock(x0=100, y0=250, x1=300, y1=270)
        mock_good_annot.vertices = []
        mock_good_annot.info = {}
        
        mock_page = Mock()
        mock_page.annots.return_value = [mock_bad_annot, mock_good_annot]
        
        # First call raises exception, second succeeds
        mock_page.get_text.side_effect = [Exception("Error"), "Good text"]
        
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz_open.return_value = mock_doc
        
        with HighlightExtractor("test.pdf") as extractor:
            result = extractor.extract_highlights()
        
        # Should have extracted the good annotation despite the error
        assert result['total_highlights'] == 1
        assert result['highlights'][0]['text'] == "Good text"


class TestExtractHighlightsFromPdf:
    """Tests for convenience function."""
    
    @patch('src.extractor.HighlightExtractor')
    def test_convenience_function(self, mock_extractor_class):
        """Test that convenience function works correctly."""
        mock_instance = Mock()
        mock_instance.extract_highlights.return_value = {
            'total_highlights': 1,
            'highlights': []
        }
        mock_extractor_class.return_value.__enter__.return_value = mock_instance
        mock_extractor_class.return_value.__exit__.return_value = None
        
        result = extract_highlights_from_pdf("test.pdf")
        
        assert result['total_highlights'] == 1
        mock_extractor_class.assert_called_once_with("test.pdf")
        mock_instance.extract_highlights.assert_called_once()
