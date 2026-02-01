# Quick Start Guide

Get up and running with Highext in minutes.

## Installation

1. **Install the package:**
   ```bash
   pip install .
   ```

## Basic Usage

### Run the TUI (Interactive Mode):
```bash
highext
```
This opens the Text User Interface where you can browse files and extract highlights interactively.
**New:** The TUI now displays a live preview of extracted highlights with their actual colors!
**Tip:** You can press `Escape` to exit input fields (like the filename box).

### Extract highlights from a PDF (CLI):
```bash
highext-cli your_document.pdf -f json -o highlights.json
```
This will create a `highlights.json` file with all the extracted highlights.

To get a pretty-printed JSON, add the `-p` flag:
```bash
highext-cli your_document.pdf -f json -o highlights.json -p
```

### Export highlights to XMind mindmap:
```bash
highext-cli your_document.pdf -f xmind -o mindmap.xmind
```
This creates a visual `mindmap.xmind` file that you can open in XMind.

### Export highlights to Notion-compatible Markdown:
```bash
highext-cli your_document.pdf -f notion -o highlights.md
```
This generates a Markdown file optimized for Notion import, with colored text matching the PDF.

## Common Commands

### Enable detailed logging:
```bash
highext-cli document.pdf -f json -o results.json -v
```

### Organize results by color (affects XMind and Notion):
```bash
highext-cli document.pdf -f xmind -o mindmap.xmind --group-by color
```

## Running Tests

### Run all tests:
```bash
pytest tests/
```

### Run tests with coverage:
```bash
pytest --cov=src tests/
```

### Run specific test file:
```bash
pytest tests/test_extractor.py -v
```

## Testing with Example PDF

1. Create a PDF with highlights using any PDF reader (Adobe Acrobat, Preview, etc.)
2. Save it as `examples/sample.pdf`
3. Run the extractor:
   ```bash
   highext-cli examples/sample.pdf -o examples/output.json -v -p
   ```
4. Check the results:
   ```bash
   cat examples/output.json
   ```

See [`examples/README.md`](examples/README.md) for detailed instructions on creating test PDFs.

## What Gets Extracted?

The tool extracts:
- ✅ Text content from highlights
- ✅ Page numbers
- ✅ Highlight colors (RGB and color names)
- ✅ Bounding box coordinates
- ✅ Author information (if available)
- ✅ Creation timestamps (if available)

## XMind Mindmap Export

The `--xmind` option creates a visual mindmap of your highlights:
- 🗂️ Organize by **page** (default) or by **color**
- 🎨 Color-coded markers for different highlight colors
- 📝 Full text and metadata stored in topic notes
- 🧠 Visual representation perfect for studying and reviewing

Open the `.xmind` file in [XMind](https://www.xmind.net/) (free version available) to explore your highlights visually.

## Troubleshooting

### "No highlights found"
- Make sure your PDF has actual highlight annotations
- Colored text or background colors are NOT highlights
- Try creating highlights in a different PDF editor

### "File not found"
- Check the file path is correct
- Use absolute paths if having issues with relative paths

### Import errors
- Ensure PyMuPDF is installed: `pip install PyMuPDF`
- Check Python version: `python --version` (must be 3.12+)

## Next Steps

- Read the full [`README.md`](README.md) for detailed documentation
- Check [`plans/architecture.md`](plans/architecture.md) for technical details
- Explore the test files in [`tests/`](tests/) for usage examples

## Need Help?

- Review the help message: `highext-cli --help`
- Check the examples in the [`examples/`](examples/) directory
- Read the architecture documentation in [`plans/architecture.md`](plans/architecture.md)
