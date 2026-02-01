"""Tests for Notion exporter module."""

import json
from pathlib import Path
import pytest
from src.notion_exporter import NotionExporter, export_to_notion


@pytest.fixture
def sample_data():
    """Sample highlight data for testing."""
    return {
        "source_path": "/path/to/document.pdf",
        "extraction_date": "2026-01-31T22:00:00Z",
        "total_pages": 2,
        "total_highlights": 3,
        "highlights": [
            {
                "page": 1,
                "text": "First highlight on page 1",
                "color": [1.0, 1.0, 0.0],
                "color_name": "yellow",
                "rect": [100.0, 200.0, 300.0, 220.0]
            },
            {
                "page": 1,
                "text": "Second highlight on page 1",
                "color": [1.0, 0.0, 0.0],
                "color_name": "red",
                "rect": [100.0, 250.0, 300.0, 270.0]
            },
            {
                "page": 2,
                "text": "Highlight on page 2",
                "color": [0.0, 1.0, 0.0],
                "color_name": "green",
                "rect": [100.0, 150.0, 300.0, 170.0]
            }
        ]
    }


def test_notion_exporter_initialization(sample_data):
    """Test NotionExporter initialization."""
    exporter = NotionExporter(sample_data)
    assert exporter.data == sample_data


def test_generate_markdown(sample_data):
    """Test Markdown generation."""
    exporter = NotionExporter(sample_data)
    markdown = exporter._generate_markdown(group_by='page')
    
    # Check title
    assert "# document" in markdown
    
    # Check metadata section
    assert "## Document Information" in markdown
    assert "**Source:**" in markdown
    assert "**Total Pages:** 2" in markdown
    assert "**Total Highlights:** 3" in markdown
    
    # Check highlights section
    assert "## Highlights" in markdown
    assert "### Page 1" in markdown
    assert "### Page 2" in markdown
    
    # Check color sections
    assert "#### Yellow" in markdown or "#### Red" in markdown
    assert "#### Green" in markdown
    
    # Check highlight text (as blockquotes with color span)
    assert "> <span style=\"color: #FFFF00\">First highlight on page 1</span>" in markdown
    assert "> <span style=\"color: #FF0000\">Second highlight on page 1</span>" in markdown
    assert "> <span style=\"color: #00FF00\">Highlight on page 2</span>" in markdown


def test_generate_markdown_no_highlights():
    """Test Markdown generation with no highlights."""
    data = {
        "source_path": "/path/to/empty.pdf",
        "extraction_date": "2026-01-31T22:00:00Z",
        "total_pages": 1,
        "total_highlights": 0,
        "highlights": []
    }
    
    exporter = NotionExporter(data)
    markdown = exporter._generate_markdown(group_by='page')
    
    assert "# empty" in markdown
    assert "## Highlights" in markdown
    assert "*No highlights found in this document.*" in markdown


def test_export_to_file(sample_data, tmp_path):
    """Test exporting to a Markdown file."""
    output_file = tmp_path / "test_output.md"
    
    exporter = NotionExporter(sample_data)
    exporter.export(output_file, group_by='page')
    
    # Check file was created
    assert output_file.exists()
    
    # Check file content
    content = output_file.read_text(encoding='utf-8')
    assert "# document" in content
    assert "## Highlights" in content
    assert "> <span style=\"color: #FFFF00\">First highlight on page 1</span>" in content


def test_export_to_notion_function(sample_data, tmp_path):
    """Test the export_to_notion convenience function."""
    output_file = tmp_path / "notion_export.md"
    
    export_to_notion(sample_data, output_file, group_by='page')
    
    # Check file was created
    assert output_file.exists()
    
    # Check file content
    content = output_file.read_text(encoding='utf-8')
    assert "## Document Information" in content
    assert "### Page 1" in content


def test_markdown_structure_order(sample_data):
    """Test that Markdown structure follows correct order."""
    exporter = NotionExporter(sample_data)
    markdown = exporter._generate_markdown(group_by='page')
    
    # Find positions of key sections
    title_pos = markdown.find("# document")
    info_pos = markdown.find("## Document Information")
    highlights_pos = markdown.find("## Highlights")
    page1_pos = markdown.find("### Page 1")
    page2_pos = markdown.find("### Page 2")
    
    # Verify order
    assert title_pos < info_pos < highlights_pos < page1_pos < page2_pos


def test_color_grouping_within_page(sample_data):
    """Test that colors are grouped within each page."""
    exporter = NotionExporter(sample_data)
    markdown = exporter._generate_markdown(group_by='page')
    
    # Split by pages
    page1_section = markdown.split("### Page 1")[1].split("### Page 2")[0]
    
    # Check that both yellow and red are in page 1 section
    assert "#### Yellow" in page1_section or "#### Red" in page1_section
    assert "> <span style=\"color: #FFFF00\">First highlight on page 1</span>" in page1_section
    assert "> <span style=\"color: #FF0000\">Second highlight on page 1</span>" in page1_section
