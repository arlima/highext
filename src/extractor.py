"""Core PDF annotation extraction logic."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from .utils import rgb_to_color_name

logger = logging.getLogger(__name__)


class HighlightExtractor:
    """Extract highlighted text from PDF files."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the extractor.
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = pdf_path
        self.doc = None
    
    def __enter__(self):
        """Context manager entry."""
        self.doc = fitz.open(self.pdf_path)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.doc:
            self.doc.close()
    
    def extract_highlights(self) -> dict[str, Any]:
        """
        Extract all highlights from the PDF.
        
        Returns:
            Dictionary containing extraction results and metadata
        """
        if not self.doc:
            raise RuntimeError("Document not opened. Use context manager.")
        
        highlights = []
        
        logger.info(f"Processing PDF: {self.pdf_path}")
        logger.info(f"Total pages: {len(self.doc)}")
        
        for page_num in range(len(self.doc)):
            page = self.doc[page_num]
            page_highlights = self._extract_page_highlights(page, page_num + 1)
            highlights.extend(page_highlights)
            
            if page_highlights:
                logger.debug(f"Page {page_num + 1}: Found {len(page_highlights)} highlights")
        
        logger.info(f"Total highlights extracted: {len(highlights)}")
        
        return {
            "source_file": str(Path(self.pdf_path).name),
            "source_path": str(Path(self.pdf_path).absolute()),
            "extraction_date": datetime.now(timezone.utc).isoformat(),
            "total_pages": len(self.doc),
            "total_highlights": len(highlights),
            "highlights": highlights
        }
    
    def _extract_page_highlights(self, page: fitz.Page, page_num: int) -> list[dict[str, Any]]:
        """
        Extract highlights from a single page.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (1-indexed)
            
        Returns:
            List of highlight dictionaries
        """
        highlights = []
        
        try:
            annots = page.annots()
            if not annots:
                return highlights
            
            for annot in annots:
                try:
                    # Type 8 is Highlight annotation
                    if annot.type[0] == 8:
                        highlight_data = self._extract_highlight_data(page, annot, page_num)
                        if highlight_data:
                            highlights.append(highlight_data)
                except Exception as e:
                    logger.warning(f"Error processing annotation on page {page_num}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error accessing annotations on page {page_num}: {e}")
        
        return highlights
    
    def _extract_highlight_data(
        self, 
        page: fitz.Page, 
        annot: fitz.Annot, 
        page_num: int
    ) -> dict[str, Any] | None:
        """
        Extract data from a single highlight annotation.
        
        Args:
            page: PyMuPDF page object
            annot: Annotation object
            page_num: Page number (1-indexed)
            
        Returns:
            Dictionary with highlight data or None if extraction failed
        """
        try:
            # Get the highlighted text
            text = self._get_highlight_text(page, annot)
            
            if not text or not text.strip():
                logger.debug(f"Empty text in highlight on page {page_num}")
                return None
            
            # Get color information
            color = annot.colors.get("stroke")
            if color is None:
                color = annot.colors.get("fill", [1.0, 1.0, 0.0])  # Default to yellow
            
            # Convert to RGB tuple if needed
            if isinstance(color, dict):
                color = [1.0, 1.0, 0.0]  # Default to yellow
            
            # Ensure we have 3 color components
            if len(color) < 3:
                if len(color) == 1:
                    # Grayscale to RGB
                    val = color[0]
                    color = [val, val, val]
                else:
                    color = list(color) + [0.0] * (3 - len(color))
            color = color[:3]
            
            # Get bounding rectangle
            rect = annot.rect
            rect_coords = [rect.x0, rect.y0, rect.x1, rect.y1]
            
            # Get optional metadata
            info = annot.info
            author = info.get("title") or info.get("subject") or None
            
            # Get creation date
            created = None
            if "creationDate" in info:
                try:
                    created = info["creationDate"]
                except Exception:
                    pass
            
            return {
                "page": page_num,
                "text": text.strip(),
                "color": color,
                "color_name": rgb_to_color_name(tuple(color)),
                "rect": rect_coords,
                "author": author,
                "created": created
            }
            
        except Exception as e:
            logger.warning(f"Error extracting highlight data on page {page_num}: {e}")
            return None
    
    def _get_highlight_text(self, page: fitz.Page, annot: fitz.Annot) -> str:
        """
        Extract text from a highlighted area.
        
        Args:
            page: PyMuPDF page object
            annot: Annotation object
            
        Returns:
            Extracted text
        """
        try:
            # Get all highlight rectangles (there can be multiple for multi-line highlights)
            text_parts = []
            
            # Try to get vertices (quadpoints) for more accurate text extraction
            vertices = annot.vertices
            if vertices and len(vertices) >= 4:
                # Group vertices into quads (4 points each)
                for i in range(0, len(vertices), 4):
                    if i + 3 < len(vertices):
                        quad = vertices[i:i+4]
                        # Create a rectangle from the quad points
                        xs = [p[0] for p in quad]
                        ys = [p[1] for p in quad]
                        rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
                        
                        # Extract text from this rectangle
                        text = page.get_text("text", clip=rect)
                        if text.strip():
                            text_parts.append(text.strip())
            
            # Fallback to annotation rectangle if no vertices
            if not text_parts:
                rect = annot.rect
                text = page.get_text("text", clip=rect)
                if text.strip():
                    text_parts.append(text.strip())
            
            # Join all parts
            return " ".join(text_parts)
            
        except Exception as e:
            logger.warning(f"Error extracting text from highlight: {e}")
            # Final fallback to just the rect
            try:
                rect = annot.rect
                return page.get_text("text", clip=rect).strip()
            except Exception:
                return ""


def extract_highlights_from_pdf(pdf_path: str) -> dict[str, Any]:
    """
    Convenience function to extract highlights from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing extraction results
    """
    with HighlightExtractor(pdf_path) as extractor:
        return extractor.extract_highlights()
