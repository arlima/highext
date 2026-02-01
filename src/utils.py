"""Utility functions for JSON formatting, color conversion, and validation."""

import json
import os
from pathlib import Path
from typing import Any


def rgb_to_color_name(rgb: tuple[float, float, float]) -> str:
    """
    Convert RGB values to the closest standard color name.
    
    Args:
        rgb: Tuple of RGB values (0.0 to 1.0 range)
        
    Returns:
        Color name as string
    """
    if not rgb or len(rgb) < 3:
        return "unknown"

    # Expanded color map with common PDF highlight colors and standard colors
    # Values are in 0.0-1.0 range
    known_colors = {
        # Standard PDF/Office Highlight Colors
        "Yellow": (1.0, 1.0, 0.0),      # Standard Yellow
        "Red": (1.0, 0.0, 0.0),         # Standard Red
        "Green": (0.0, 1.0, 0.0),       # Standard Green
        "Blue": (0.0, 0.0, 1.0),        # Standard Blue
        "Orange": (1.0, 0.5, 0.0),      # Standard Orange
        "Magenta": (1.0, 0.0, 1.0),     # Standard Magenta
        "Cyan": (0.0, 1.0, 1.0),        # Standard Cyan
        "Purple": (0.5, 0.0, 0.5),      # Standard Purple
        "Pink": (1.0, 0.75, 0.8),       # Standard Pink
        
        # Soft/Pastel Variants (Common in Mac Preview/PDF Readers)
        "Light Yellow": (1.0, 0.98, 0.6),
        "Light Green": (0.6, 1.0, 0.6),
        "Light Blue": (0.6, 0.8, 1.0),
        "Light Pink": (1.0, 0.7, 0.7),
        "Light Purple": (0.8, 0.6, 0.8),
        "Light Orange": (1.0, 0.8, 0.4),
        "Light Gray": (0.9, 0.9, 0.9),
        
        # Additional Common Colors
        "Dark Red": (0.5, 0.0, 0.0),
        "Dark Green": (0.0, 0.5, 0.0),
        "Dark Blue": (0.0, 0.0, 0.5),
        "Gray": (0.5, 0.5, 0.5),
        "Black": (0.0, 0.0, 0.0),
        "White": (1.0, 1.0, 1.0),
        "Teal": (0.0, 0.5, 0.5),
        "Olive": (0.5, 0.5, 0.0),
        "Maroon": (0.5, 0.0, 0.0),
        "Navy": (0.0, 0.0, 0.5),
        "Lime": (0.0, 1.0, 0.0),      # Same as Green, but good to have if slightly off
        "Gold": (1.0, 0.84, 0.0),
        "Salmon": (0.98, 0.5, 0.45),
        "Sky Blue": (0.53, 0.81, 0.92),
    }

    r, g, b = rgb[:3]
    
    # Check saturation (difference between max and min channel)
    # If the color has significant saturation, avoid matching with grayscale colors
    saturation = max(r, g, b) - min(r, g, b)
    is_chromatic = saturation > 0.15  # Threshold for "having color"

    # Find closest color using Euclidean distance
    min_dist = float('inf')
    closest_name = "Gray"  # Default fallback
    
    grayscale_names = {"Gray", "Light Gray", "Black", "White"}
    
    for name, (cr, cg, cb) in known_colors.items():
        # If input is chromatic, skip grayscale targets unless they are the only option
        # (which won't happen as we have plenty of colors)
        if is_chromatic and name in grayscale_names:
            continue
            
        # Calculate squared Euclidean distance (no need for sqrt for comparison)
        dist = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        
        if dist < min_dist:
            min_dist = dist
            closest_name = name
            
    # If distance is very small, return the name directly
    # Otherwise, we could format it, but sticking to the closest name is usually best for categorization
    
    return closest_name


def rgb_to_hex(rgb: list[float] | tuple[float, ...]) -> str:
    """
    Convert RGB (0.0-1.0) to HEX string.
    
    Args:
        rgb: List or Tuple of RGB values
        
    Returns:
        HEX color string (e.g. "#FF0000")
    """
    if not rgb or len(rgb) < 3:
        return "#FFFFFF"
    r, g, b = rgb[:3]
    
    # Handle 0-255 scale if detected
    if r > 1.0 or g > 1.0 or b > 1.0:
        r /= 255.0
        g /= 255.0
        b /= 255.0
        
    # Clamp to 0.0-1.0
    r = max(0.0, min(1.0, r))
    g = max(0.0, min(1.0, g))
    b = max(0.0, min(1.0, b))
    
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def group_highlights(highlights: list[dict[str, Any]], group_by: str) -> dict[str, list[dict[str, Any]]]:
    """
    Group highlights by page or color.
    
    Args:
        highlights: List of highlight dictionaries
        group_by: 'page' or 'color'
        
    Returns:
        Dictionary mapping keys (page number or color) to lists of highlights
    """
    grouped = {}
    if group_by == "page":
        for h in highlights:
            key = str(h.get('page', 0))
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(h)
    elif group_by == "color":
        for h in highlights:
            key = h.get('color_name', 'unknown')
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(h)
    return grouped


def format_json_output(data: dict[str, Any], pretty: bool = False, group_by: str | None = None) -> str:
    """
    Format data as JSON string.
    
    Args:
        data: Dictionary to format
        pretty: Whether to pretty-print the JSON
        group_by: Optional grouping ('page' or 'color')
        
    Returns:
        JSON formatted string
    """
    output_data = data.copy()
    
    if group_by and 'highlights' in output_data:
        output_data['grouped_highlights'] = group_highlights(output_data['highlights'], group_by)
        
    if pretty:
        return json.dumps(output_data, indent=2, ensure_ascii=False)
    return json.dumps(output_data, ensure_ascii=False)


def validate_pdf_file(path: str) -> tuple[bool, str]:
    """
    Validate if the file exists and is a PDF.
    
    Args:
        path: Path to the file to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    file_path = Path(path)
    
    if not file_path.exists():
        return False, f"File not found: {path}"
    
    if not file_path.is_file():
        return False, f"Path is not a file: {path}"
    
    if file_path.suffix.lower() != '.pdf':
        return False, f"File is not a PDF: {path}"
    
    if not os.access(path, os.R_OK):
        return False, f"File is not readable: {path}"
    
    return True, ""


def validate_output_path(path: str) -> tuple[bool, str]:
    """
    Validate if the output path is writable.
    
    Args:
        path: Path to the output file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    output_path = Path(path)
    
    # Check if parent directory exists
    parent_dir = output_path.parent
    if not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return False, f"Cannot create output directory: {e}"
    
    # Check if file already exists and is writable
    if output_path.exists() and not os.access(path, os.W_OK):
        return False, f"Output file is not writable: {path}"
    
    return True, ""
