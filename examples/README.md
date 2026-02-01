# Examples

This directory contains example files for testing the PDF highlight extractor.

## Files

- **sample.pdf**: Example PDF file with various highlights (to be added by the user)
- **expected_output.json**: Example of the expected JSON output format

## How to Create a Test PDF

To test the extractor, you'll need a PDF file with highlights. Here's how to create one:

### Using Adobe Acrobat Reader

1. Open any PDF file in Adobe Acrobat Reader
2. Click the "Comment" tool in the toolbar
3. Select "Highlight Text" tool
4. Click and drag over text to highlight it
5. Repeat with different colors if desired
6. Save the file as `sample.pdf` in this directory

### Using Preview (macOS)

1. Open any PDF file in Preview
2. Click the "Markup" toolbar button
3. Select the "Highlight" tool
4. Click and drag over text to highlight it
5. Change colors using the color selector
6. Save the file as `sample.pdf` in this directory

### Using PDF Editors

Many PDF editors support adding highlights:
- Foxit Reader
- PDF-XChange Editor
- Okular (Linux)
- Xodo (mobile)

## Testing the Extractor

Once you have a PDF with highlights:

```bash
# Extract highlights
python -m src.cli examples/sample.pdf -o examples/output.json -v -p

# View the results
cat examples/output.json
```

The output should contain all highlighted text with metadata similar to the format shown in `expected_output.json`.

## Notes

- The extractor only works with actual PDF highlight annotations
- Colored text or background colors are NOT considered highlights
- Different PDF editors may create slightly different annotation formats
- Test with multiple PDF sources if you encounter issues
