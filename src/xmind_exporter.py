"""XMind mindmap exporter for PDF highlights (JSON format for XMind 2020+)."""

import json
import logging
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .utils import rgb_to_hex

logger = logging.getLogger(__name__)


class XMindExporter:
    """Export PDF highlights to XMind mindmap format."""
    
    def __init__(self, highlights_data: dict[str, Any]):
        """
        Initialize the exporter.
        
        Args:
            highlights_data: Dictionary containing extraction results
        """
        self.data = highlights_data

    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4()).replace('-', '')[:16]

    def _get_timestamp(self) -> str:
        """Get current timestamp in milliseconds."""
        return str(int(datetime.now().timestamp() * 1000))

    def export(self, output_path: str, group_by: str = "page") -> None:
        """
        Export highlights to XMind format.
        
        Args:
            output_path: Path to save the XMind file
            group_by: How to organize highlights ("page" or "color")
        """
        logger.info(f"Creating XMind mindmap (JSON): {output_path}")
        
        if group_by not in ["page", "color"]:
            raise ValueError(f"Invalid group_by option: {group_by}")
        
        # Create content
        content = self._create_content(group_by)
        manifest = self._create_manifest()
        metadata = self._create_metadata()
        
        # Write to ZIP file
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('content.json', json.dumps(content, indent=2))
                zf.writestr('manifest.json', json.dumps(manifest, indent=2))
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            
            logger.info(f"XMind file saved: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save XMind file: {e}")
            raise

    def _create_content(self, group_by: str) -> list[dict[str, Any]]:
        """Create the content structure."""
        
        source_file = self.data.get('source_file', 'PDF Highlights')
        if source_file != 'PDF Highlights':
            source_file = Path(source_file).stem

        # Root topic
        root_topic = {
            "id": self._generate_id(),
            "class": "topic",
            "title": source_file,
            "structureClass": "org.xmind.ui.map.unbalanced",
            "children": {
                "attached": []
            }
        }
        
        # Add metadata as notes
        root_topic["notes"] = {
            "plain": {
                "content": self._create_metadata_text()
            }
        }

        # Populate children
        attached = root_topic["children"]["attached"]
        if group_by == "page":
            self._add_page_topics(attached)
        else:
            self._add_color_topics(attached)

        # Sheet
        sheet = {
            "id": self._generate_id(),
            "class": "sheet",
            "title": f"Highlights: {source_file}",
            "rootTopic": root_topic
        }
        
        return [sheet]

    def _add_page_topics(self, attached_list: list[dict[str, Any]]) -> None:
        """Add topics organized by page."""
        highlights = self.data.get('highlights', [])
        if not highlights:
            attached_list.append({"id": self._generate_id(), "title": "No highlights found"})
            return

        # Group by page
        pages = {}
        for highlight in highlights:
            page_num = highlight.get('page', 0)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(highlight)

        for page_num in sorted(pages.keys()):
            page_highlights = pages[page_num]
            
            page_topic = {
                "id": self._generate_id(),
                "title": f"Page {page_num}",
                "children": {"attached": []}
            }
            attached_list.append(page_topic)
            
            # Group by color within page
            colors_in_page = {}
            for highlight in page_highlights:
                color_name = highlight.get('color_name', 'unknown')
                if color_name not in colors_in_page:
                    colors_in_page[color_name] = []
                colors_in_page[color_name].append(highlight)
            
            for color_name in sorted(colors_in_page.keys()):
                color_highlights = colors_in_page[color_name]
                
                # Group topic style
                first_color = color_highlights[0].get('color', [])
                hex_color = rgb_to_hex(first_color)
                
                color_topic = {
                    "id": self._generate_id(),
                    "title": color_name.title(),
                    "style": {
                        "properties": {
                            "svg:fill": hex_color,
                            "fill": hex_color,
                            "shape-class": "org.xmind.topicShape.roundedRect",
                            "border-line-color": hex_color,
                            "line-color": hex_color
                        }
                    },
                    "children": {"attached": []}
                }
                page_topic["children"]["attached"].append(color_topic)
                
                for highlight in color_highlights:
                    self._add_highlight_topic(color_topic["children"]["attached"], highlight)

    def _add_color_topics(self, attached_list: list[dict[str, Any]]) -> None:
        """Add topics organized by color."""
        highlights = self.data.get('highlights', [])
        if not highlights:
            attached_list.append({"id": self._generate_id(), "title": "No highlights found"})
            return

        # Group by color
        colors = {}
        for highlight in highlights:
            color_name = highlight.get('color_name', 'unknown')
            if color_name not in colors:
                colors[color_name] = []
            colors[color_name].append(highlight)

        for color_name in sorted(colors.keys()):
            color_highlights = colors[color_name]
            
            # Group topic style
            first_color = color_highlights[0].get('color', [])
            hex_color = rgb_to_hex(first_color)
            
            color_topic = {
                "id": self._generate_id(),
                "title": color_name.title(),
                "style": {
                    "properties": {
                        "svg:fill": hex_color,
                        "fill": hex_color,
                        "shape-class": "org.xmind.topicShape.roundedRect",
                        "border-line-color": hex_color,
                        "line-color": hex_color
                    }
                },
                "children": {"attached": []}
            }
            attached_list.append(color_topic)
            
            # Group by page within color
            pages = {}
            for highlight in color_highlights:
                page_num = highlight.get('page', 0)
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(highlight)
            
            for page_num in sorted(pages.keys()):
                page_highlights = pages[page_num]
                
                page_topic = {
                    "id": self._generate_id(),
                    "title": f"Page {page_num}",
                    "children": {"attached": []}
                }
                color_topic["children"]["attached"].append(page_topic)
                
                for highlight in page_highlights:
                    self._add_highlight_topic(page_topic["children"]["attached"], highlight)

    def _add_highlight_topic(self, attached_list: list[dict[str, Any]], highlight: dict[str, Any]) -> None:
        """Add a highlight topic."""
        text = highlight.get('text', 'No text')
        color_rgb = highlight.get('color', [])
        hex_color = rgb_to_hex(color_rgb)
        
        topic = {
            "id": self._generate_id(),
            "title": text,
            "style": {
                "properties": {
                    "svg:fill": hex_color,
                    "shape-class": "org.xmind.topicShape.roundedRect",
                    "border-line-color": hex_color
                }
            }
        }
        attached_list.append(topic)

    def _create_metadata_text(self) -> str:
        """Create metadata text."""
        return (
            f"Total Pages: {self.data.get('total_pages', 'N/A')}\n"
            f"Total Highlights: {self.data.get('total_highlights', 0)}\n"
            f"Extraction Date: {self.data.get('extraction_date', 'N/A')}\n"
            f"Source Path: {self.data.get('source_path', 'N/A')}"
        )

    def _create_metadata(self) -> dict[str, Any]:
        """Create metadata dict."""
        return {
            "creator": {
                "name": "PDF Highlight Extractor",
                "version": "1.0.0"
            },
            "created": self.data.get('extraction_date', datetime.now().isoformat())
        }

    def _create_manifest(self) -> dict[str, Any]:
        """Create manifest dict."""
        return {
            "file-entries": {
                "content.json": {},
                "metadata.json": {}
            }
        }


def export_to_xmind(
    highlights_data: dict[str, Any],
    output_path: str,
    group_by: str = "page"
) -> None:
    """
    Convenience function to export highlights to XMind.
    
    Args:
        highlights_data: Dictionary containing extraction results
        output_path: Path to save the XMind file
        group_by: How to organize highlights ("page" or "color")
    """
    exporter = XMindExporter(highlights_data)
    exporter.export(output_path, group_by)
