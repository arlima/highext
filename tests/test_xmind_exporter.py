"""Tests for XMind export functionality."""

import json
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.xmind_exporter import XMindExporter, export_to_xmind


class TestXMindExporter:
    """Tests for XMindExporter class."""
    
    def setup_method(self):
        """Set up test data."""
        self.sample_data = {
            'source_file': 'test.pdf',
            'source_path': '/path/to/test.pdf',
            'extraction_date': '2026-01-31T21:00:00Z',
            'total_pages': 2,
            'total_highlights': 3,
            'highlights': [
                {
                    'page': 1,
                    'text': 'First highlight',
                    'color': [1.0, 1.0, 0.0],
                    'color_name': 'Yellow',
                    'rect': [100, 200, 300, 220],
                    'author': 'Test User',
                    'created': 'D:20260131210000'
                },
                {
                    'page': 1,
                    'text': 'Second highlight',
                    'color': [1.0, 0.0, 0.0],
                    'color_name': 'Red',
                    'rect': [100, 250, 300, 270],
                    'author': None,
                    'created': None
                },
                {
                    'page': 2,
                    'text': 'Third highlight',
                    'color': [0.0, 1.0, 0.0],
                    'color_name': 'Green',
                    'rect': [50, 150, 400, 170],
                    'author': None,
                    'created': None
                }
            ]
        }
    
    def test_export_creates_valid_zip(self, tmp_path):
        """Test that export creates a valid ZIP file."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='page')
        
        assert output_file.exists()
        assert zipfile.is_zipfile(output_file)
    
    def test_export_contains_required_files(self, tmp_path):
        """Test that ZIP contains required files."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='page')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            names = zf.namelist()
            assert 'content.json' in names
            assert 'manifest.json' in names
            assert 'metadata.json' in names
    
    def test_export_by_page_structure(self, tmp_path):
        """Test export organized by page."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='page')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            content_json = zf.read('content.json').decode('utf-8')
            content = json.loads(content_json)
            
            # Root topic title should be filename stem
            sheet = content[0]
            root_topic = sheet['rootTopic']
            assert root_topic['title'] == 'test'
            
            # Check structure
            attached = root_topic['children']['attached']
            # Should have page topics
            page_topics = [t for t in attached if t['title'].startswith('Page ')]
            assert len(page_topics) > 0
    
    def test_export_by_color_structure(self, tmp_path):
        """Test export organized by color."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='color')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            content_json = zf.read('content.json').decode('utf-8')
            content = json.loads(content_json)
            
            sheet = content[0]
            root_topic = sheet['rootTopic']
            attached = root_topic['children']['attached']
            
            # Should contain color names in the topics
            titles = [t['title'] for t in attached]
            assert 'Yellow' in titles
            assert 'Red' in titles
            assert 'Green' in titles
    
    def test_export_empty_highlights(self, tmp_path):
        """Test export with no highlights."""
        empty_data = {
            'source_file': 'empty.pdf',
            'source_path': '/path/to/empty.pdf',
            'extraction_date': '2026-01-31T21:00:00Z',
            'total_pages': 5,
            'total_highlights': 0,
            'highlights': []
        }
        
        output_file = tmp_path / "empty.xmind"
        exporter = XMindExporter(empty_data)
        exporter.export(str(output_file), group_by='page')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            content_json = zf.read('content.json').decode('utf-8')
            content = json.loads(content_json)
            
            sheet = content[0]
            root_topic = sheet['rootTopic']
            attached = root_topic['children']['attached']
            assert any(t['title'] == 'No highlights found' for t in attached)
    
    def test_create_metadata_text(self):
        """Test metadata text generation."""
        exporter = XMindExporter(self.sample_data)
        metadata = exporter._create_metadata_text()
        
        assert 'Total Pages: 2' in metadata
        assert 'Total Highlights: 3' in metadata
        assert '2026-01-31T21:00:00Z' in metadata
        assert '/path/to/test.pdf' in metadata
    
    
    def test_invalid_group_by(self):
        """Test that invalid group_by raises error."""
        exporter = XMindExporter(self.sample_data)
        
        with pytest.raises(ValueError, match="Invalid group_by option"):
            exporter.export('test.xmind', group_by='invalid')
    
    def test_generate_id_unique(self):
        """Test that generated IDs are unique."""
        exporter = XMindExporter(self.sample_data)
        
        id1 = exporter._generate_id()
        id2 = exporter._generate_id()
        
        assert id1 != id2
        assert len(id1) == 16
        assert len(id2) == 16
    
    def test_json_structure_valid(self, tmp_path):
        """Test that generated JSON is valid."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='page')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            content_json = zf.read('content.json').decode('utf-8')
            manifest_json = zf.read('manifest.json').decode('utf-8')
            
            # Should be valid JSON
            content = json.loads(content_json)
            manifest = json.loads(manifest_json)
            
            assert isinstance(content, list)
            assert isinstance(manifest, dict)
    
    def test_metadata_json_structure(self, tmp_path):
        """Test metadata.json structure."""
        output_file = tmp_path / "test.xmind"
        exporter = XMindExporter(self.sample_data)
        exporter.export(str(output_file), group_by='page')
        
        with zipfile.ZipFile(output_file, 'r') as zf:
            metadata_json = zf.read('metadata.json').decode('utf-8')
            metadata = json.loads(metadata_json)
            
            assert 'creator' in metadata
            assert 'name' in metadata['creator']
            assert 'version' in metadata['creator']
            # created/time might vary in format/key depending on implementation details
    
    
class TestExportToXmind:
    """Tests for convenience function."""
    
    def test_convenience_function(self, tmp_path):
        """Test that convenience function works correctly."""
        output_file = tmp_path / "output.xmind"
        test_data = {
            'source_file': 'test.pdf',
            'total_pages': 1,
            'total_highlights': 0,
            'highlights': []
        }
        
        export_to_xmind(test_data, str(output_file), group_by='page')
        
        assert output_file.exists()
        assert zipfile.is_zipfile(output_file)
    
    def test_convenience_function_with_color(self, tmp_path):
        """Test convenience function with color grouping."""
        output_file = tmp_path / "output.xmind"
        test_data = {
            'source_file': 'test.pdf',
            'total_pages': 1,
            'total_highlights': 0,
            'highlights': []
        }
        
        export_to_xmind(test_data, str(output_file), group_by='color')
        
        assert output_file.exists()
