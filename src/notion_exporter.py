"""
Notion Exporter Module

This module provides functionality to export PDF highlights to Markdown format
that can be imported into Notion as a note.
"""

import logging
from pathlib import Path
from typing import Any

from .utils import rgb_to_hex

logger = logging.getLogger(__name__)


class NotionExporter:
    """Export PDF highlights to Notion-compatible Markdown format."""
    
    def __init__(self, data: dict[str, Any]):
        """
        Initialize the Notion exporter.
        
        Args:
            data: Dictionary containing PDF highlights data
        """
        self.data = data
    
    def export(self, output_path: str | Path, group_by: str = "page") -> None:
        """
        Export highlights to a Markdown file for Notion import.
        
        Args:
            output_path: Path where the Markdown file should be saved
            group_by: How to organize highlights ("page" or "color")
        """
        output_path = Path(output_path)
        
        try:
            markdown_content = self._generate_markdown(group_by)
            
            # Write to file
            output_path.write_text(markdown_content, encoding='utf-8')
            logger.info(f"Successfully exported highlights to Notion-compatible Markdown: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export to Notion format: {e}")
            raise
    
    def _generate_markdown(self, group_by: str) -> str:
        """Generate Markdown content from highlights data."""
        lines = []
        
        # Add title
        source_path = self.data.get('source_path', 'Unknown PDF')
        filename = Path(source_path).stem if source_path != 'Unknown PDF' else source_path
        lines.append(f"# {filename}\n")
        
        # Add metadata
        lines.append("## Document Information\n")
        lines.append(f"- **Source:** {source_path}")
        lines.append(f"- **Total Pages:** {self.data.get('total_pages', 'N/A')}")
        lines.append(f"- **Total Highlights:** {self.data.get('total_highlights', 0)}")
        lines.append(f"- **Extraction Date:** {self.data.get('extraction_date', 'N/A')}\n")
        
        # Get highlights
        highlights = self.data.get('highlights', [])
        
        if not highlights:
            lines.append("## Highlights\n")
            lines.append("*No highlights found in this document.*\n")
            return "\n".join(lines)
        
        # Add highlights section
        lines.append("## Highlights\n")

        if group_by == "page":
            # Group by page, then color
            pages = {}
            for highlight in highlights:
                page_num = highlight.get('page', 0)
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(highlight)
            
            for page_num in sorted(pages.keys()):
                page_highlights = pages[page_num]
                lines.append(f"### Page {page_num}\n")
                
                colors = {}
                for highlight in page_highlights:
                    color_name = highlight.get('color_name', 'unknown')
                    if color_name not in colors:
                        colors[color_name] = []
                    colors[color_name].append(highlight)
                
                for color_name in sorted(colors.keys()):
                    color_highlights = colors[color_name]
                    lines.append(f"#### {color_name.title()}\n")
                    for highlight in color_highlights:
                        text = highlight.get('text', 'No text')
                        color = highlight.get('color', [])
                        hex_color = rgb_to_hex(color)
                        
                        # Add color using HTML span
                        colored_text = f'<span style="color: {hex_color}">{text}</span>'
                        lines.append(f"> {colored_text}\n")

        else: # group_by == "color"
            # Group by color, then page
            colors = {}
            for highlight in highlights:
                color_name = highlight.get('color_name', 'unknown')
                if color_name not in colors:
                    colors[color_name] = []
                colors[color_name].append(highlight)

            for color_name in sorted(colors.keys()):
                color_highlights = colors[color_name]
                lines.append(f"### {color_name.title()}\n")

                pages = {}
                for highlight in color_highlights:
                    page_num = highlight.get('page', 0)
                    if page_num not in pages:
                        pages[page_num] = []
                    pages[page_num].append(highlight)

                for page_num in sorted(pages.keys()):
                    page_highlights = pages[page_num]
                    lines.append(f"#### Page {page_num}\n")
                    for highlight in page_highlights:
                        text = highlight.get('text', 'No text')
                        color = highlight.get('color', [])
                        hex_color = rgb_to_hex(color)
                        
                        # Add color using HTML span
                        colored_text = f'<span style="color: {hex_color}">{text}</span>'
                        lines.append(f"> {colored_text}\n")
        
        return "\n".join(lines)


def export_to_notion(data: dict[str, Any], output_path: str | Path, group_by: str = "page") -> None:
    """
    Export PDF highlights to Notion-compatible Markdown format.
    
    Args:
        data: Dictionary containing PDF highlights data
        output_path: Path where the Markdown file should be saved
        group_by: How to organize highlights ("page" or "color")
    """
    exporter = NotionExporter(data)
    exporter.export(output_path, group_by)
