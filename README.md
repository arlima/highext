# Highext

A Python CLI tool that extracts highlighted text from PDF files and outputs the results in multiple formats including JSON, XMind mindmaps, and Notion-compatible Markdown.

## Features

- ✨ Extract all highlighted text from PDF files
- 📄 Output in structured JSON format (optionally grouped)
- 🧠 Export to XMind mindmap format (.xmind)
- 📝 Export to Notion-compatible Markdown (.md) with colored text
- 🗂️ Organize highlights by page or color in all formats
- 🎨 Capture highlight colors and color names (supports 25+ standard colors)
- 📍 Record page numbers and bounding box coordinates
- 👤 Extract author and timestamp metadata when available
- 🔍 Detailed logging support
- ⚡ Fast and efficient processing with PyMuPDF
- 🖥️ TUI with colored highlight preview and improved navigation

## Requirements

- Python 3.12 or higher
- PyMuPDF (PDF processing)
- Standard Python libraries (xml, json, zipfile)
- All dependencies installed automatically with requirements.txt

## Installation

1. Clone or download this repository
2. Install the package:

```bash
pip install .
```

This will install the `highext` (TUI) and `highext-cli` (CLI) commands system-wide (or in your virtual environment).

3. (Optional) If you plan to use XMind export, ensure you have [XMind](https://www.xmind.net/) installed to open the generated mindmaps.

## Usage

### TUI (Text User Interface)

Launch the TUI with:
```bash
highext
```

- Navigate the file tree on the left. The `..` folder allows going up a directory.
- Select "Group By" Page or Color to organize exports.
- Select a PDF and click "Extract Highlights".

### CLI Usage

The basic command structure is:
`highext-cli <input.pdf> -f <format> -o <output_file>`

### Export to JSON (Default)
Extract highlights and save to a JSON file.
```bash
highext-cli document.pdf -f json -o highlights.json
```

To pretty-print the JSON output, use the `-p` or `--pretty` flag:
```bash
highext-cli document.pdf -f json -o highlights.json -p
```

### Export to XMind Mindmap
```bash
highext-cli document.pdf -f xmind -o mindmap.xmind
```

### Export to Notion-Compatible Markdown
```bash
highext-cli document.pdf -f notion -o notes.md
```

### Organize Results by Color Instead of Page
This affects the structure of XMind and Notion exports.
```bash
highext-cli document.pdf -f xmind -o mindmap.xmind --group-by color
```

### Enable Verbose Logging
```bash
highext-cli document.pdf -f json -o highlights.json -v
```

## Command-Line Options

```
positional arguments:
  input_pdf             Path to the input PDF file

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output file (e.g., highlights.json, mindmap.xmind, notes.md)
  -f {json,xmind,notion}, --format {json,xmind,notion}
                        Format of the output file
  -v, --verbose         Enable verbose logging
  -p, --pretty          Pretty-print the JSON output
  --group-by {page,color}
                        How to organize highlights in XMind or Notion exports (default: page)
  --version             show program's version number and exit
```

## Graphical Interface (TUI)

The tool includes a text-based user interface (TUI) for easier interaction. To launch it:

```bash
highext
```

This interface allows you to:
- 📂 Browse for PDF files
- ☑️ Select export formats (JSON, XMind, Notion)
- 📝 Set custom output filenames
- 📜 View extraction logs in real-time
- 👁️ Preview extracted highlights directly in the application

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "source_file": "document.pdf",
  "source_path": "/absolute/path/to/document.pdf",
  "extraction_date": "2026-01-31T21:00:00Z",
  "total_pages": 10,
  "total_highlights": 3,
  "highlights": [
    {
      "page": 1,
      "text": "This is highlighted text",
      "color": [1.0, 1.0, 0.0],
      "color_name": "yellow",
      "rect": [100.5, 200.3, 300.7, 220.8],
      "author": "John Doe",
      "created": "D:20260115103000"
    },
    {
      "page": 2,
      "text": "Another highlighted section",
      "color": [0.0, 1.0, 0.0],
      "color_name": "green",
      "rect": [50.0, 150.0, 400.0, 170.0],
      "author": null,
      "created": null
    }
  ]
}
```

### Output Fields

- **source_file**: Name of the PDF file
- **source_path**: Absolute path to the PDF file
- **extraction_date**: Timestamp of extraction (ISO 8601 UTC format)
- **total_pages**: Total number of pages in the PDF
- **total_highlights**: Number of highlights extracted
- **highlights**: Array of highlight objects with:
  - **page**: Page number (1-indexed)
  - **text**: Extracted highlighted text
  - **color**: RGB color values (0.0-1.0 range)
  - **color_name**: Human-readable color name
  - **rect**: Bounding box coordinates [x0, y0, x1, y1]
  - **author**: Author name (if available)
  - **created**: Creation date (if available)

## XMind Mindmap Format

When using the `--xmind` option, the tool creates a visual mindmap that can be opened in [XMind](https://www.xmind.net/):

### Organization Options

1. **By Page** (default): Creates a branch for each page containing its highlights
   ```
   Root: document.pdf
   ├── Page 1 (3 highlights)
   │   ├── 1. Highlighted text from page 1...
   │   ├── 2. Another highlight from page 1...
   │   └── 3. Third highlight from page 1...
   └── Page 2 (2 highlights)
       ├── 1. Highlighted text from page 2...
       └── 2. Another highlight from page 2...
   ```

2. **By Color**: Groups highlights by their color
   ```
   Root: document.pdf
   ├── Yellow (5 highlights)
   │   ├── 1. Important concept...
   │   └── ...
   ├── Red (2 highlights)
   │   └── ...
   └── Green (3 highlights)
       └── ...
   ```

### Mindmap Features

- **Root Topic**: PDF filename with metadata (pages, total highlights, extraction date)
- **Color Markers**: Visual markers based on highlight colors (yellow star, red priority, etc.)
- **Topic Notes**: Each highlight topic includes full text and metadata as notes
- **Truncated Titles**: Long text is truncated in topic titles for readability

### Opening XMind Files

1. Download [XMind](https://www.xmind.net/) (free version works)
2. Open the generated `.xmind` file
3. Explore your highlights visually in the mindmap

## Notion Export Format

When using the `--notion` option, the tool creates a Markdown file that can be imported directly into Notion:

### Markdown Structure

```markdown
# Document Name

## Document Information
- **Source:** /path/to/document.pdf
- **Total Pages:** 10
- **Total Highlights:** 15
- **Extraction Date:** 2026-01-31T22:00:00Z

## Highlights

### Page 1

#### Yellow
> First highlighted text from page 1

> Second highlighted text from page 1

#### Red
> Important note from page 1

### Page 2

#### Green
> Highlighted text from page 2
```

### Importing to Notion

1. Open Notion and navigate to the page where you want to import
2. Click the "..." menu in the top right
3. Select "Import"
4. Choose "Markdown" as the format
5. Select the generated `.md` file
6. Notion will create a new page with your highlights organized by page and color

### Features

- **Hierarchical Organization**: Highlights grouped by page, then by color
- **Blockquote Format**: Each highlight appears as a blockquote for easy reading
- **Metadata Section**: Document information at the top
- **Clean Formatting**: Ready to use in Notion without additional editing

## Project Structure

```
highext/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── __main__.py       # Module entry point
│   ├── cli.py            # CLI interface
│   ├── tui.py            # TUI interface
│   ├── extractor.py      # Core extraction logic
│   ├── xmind_exporter.py # XMind mindmap export
│   ├── notion_exporter.py # Notion Markdown export
│   └── utils.py          # Helper functions
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py # Unit tests
│   └── test_cli.py       # CLI tests
├── examples/
│   ├── sample.pdf        # Example PDF
│   └── expected_output.json
├── plans/
│   └── architecture.md   # Architecture documentation
├── requirements.txt      # Dependencies
├── .gitignore           # Git ignore patterns
└── README.md            # This file
```

## Development

### Running Tests

```bash
pytest tests/
```

### With Coverage

```bash
pytest --cov=src tests/
```

### Code Formatting

```bash
black src/ tests/
```

### Linting

```bash
flake8 src/ tests/
```

## How It Works

1. **PDF Parsing**: Opens the PDF file using PyMuPDF (fitz)
2. **Annotation Detection**: Iterates through all pages and identifies highlight annotations (type 8)
3. **Text Extraction**: Extracts text from the highlighted regions using annotation vertices or bounding rectangles
4. **Metadata Collection**: Gathers color information, coordinates, author, and creation date
5. **JSON Output**: Formats all data into a structured JSON file

## Error Handling

The tool handles various error conditions:

- **File not found**: Clear error message with file path
- **Invalid PDF**: Catches and reports PDF parsing errors
- **No highlights found**: Returns empty highlights array with warning
- **Permission errors**: Reports read/write permission issues
- **Corrupted annotations**: Skips problematic annotations and continues

## Troubleshooting

### No highlights extracted

- Ensure the PDF actually contains highlight annotations (not just colored text)
- Some PDF editors create different types of annotations
- Try opening the PDF in a viewer and verify highlights are visible

### Permission errors

- Check file permissions for both input and output files
- Ensure you have write access to the output directory

### Import errors

- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (must be 3.12+)

## Supported Highlight Colors

The tool uses a comprehensive color mapping system that recognizes over 25 standard and pastel colors, including:

- Standard: Yellow, Red, Green, Blue, Orange, Magenta, Cyan, Purple, Pink
- Pastel/Light: Light Yellow, Light Green, Light Blue, Light Pink, etc.
- Dark/Other: Dark Red, Dark Green, Gray, Teal, Olive, Navy, Maroon, etc.

The system uses nearest-neighbor matching to find the closest standard color name for any highlight, ensuring accurate and consistent naming even for custom colors. It also handles desaturated colors intelligently to distinguish between "Light Green" and "Gray".

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Author

Adriano Roberto de Lima (ARLima)

## Version

1.0.0
