"""Command-line interface for PDF highlight extractor."""

import argparse
import logging
import sys
from pathlib import Path

from .extractor import extract_highlights_from_pdf
from .utils import format_json_output, validate_pdf_file, validate_output_path
from .xmind_exporter import export_to_xmind
from .notion_exporter import export_to_notion


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: Whether to enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Extract highlighted text from PDF files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Extract highlights and save to highlights.json
  highext-cli document.pdf -o highlights.json -f json
  
  # Specify a different output file
  highext-cli document.pdf -o results.json -f json
  
  # Export to an XMind mind map
  highext-cli document.pdf -o output.xmind -f xmind
  
  # Export to Notion-compatible Markdown
  highext-cli document.pdf -o highlights.md -f notion
  
  # Group highlights by color in the export (for XMind and Notion)
  highext-cli document.pdf -o highlights.md -f notion --group-by color
  
  # Enable verbose logging
  highext-cli document.pdf -o highlights.json -f json -v
        '''
    )
    
    parser.add_argument(
        'input_pdf',
        help='Path to the input PDF file'
    )
    
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Path to the output file (e.g., highlights.json, mindmap.xmind, notes.md)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['json', 'xmind', 'notion'],
        required=True,
        help='Format of the output file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '-p', '--pretty',
        action='store_true',
        help='Pretty-print the JSON output'
    )
    
    parser.add_argument(
        '--group-by',
        choices=['page', 'color'],
        default='page',
        help='How to organize highlights in XMind or Notion exports (default: page)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='PDF Highlight Extractor 1.0.0'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_arguments()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    # Validate input file
    is_valid, error_msg = validate_pdf_file(args.input_pdf)
    if not is_valid:
        logger.error(error_msg)
        print(f"Error: {error_msg}", file=sys.stderr)
        return 1
    
    # Validate output path
    is_valid, error_msg = validate_output_path(args.output)
    if not is_valid:
        logger.error(error_msg)
        print(f"Error: {error_msg}", file=sys.stderr)
        return 1
    
    try:
        # Extract highlights
        logger.info(f"Extracting highlights from: {args.input_pdf}")
        result = extract_highlights_from_pdf(args.input_pdf)
        
        # Check if any highlights were found
        if result['total_highlights'] == 0:
            logger.warning("No highlights found in the PDF")
            print("Warning: No highlights found in the PDF", file=sys.stderr)
        
        # Process output based on the selected format
        output_path = Path(args.output)
        
        if args.format == 'json':
            logger.info("Formatting output as JSON")
            json_output = format_json_output(result, pretty=args.pretty)
            output_path.write_text(json_output, encoding='utf-8')
            
        elif args.format == 'xmind':
            logger.info("Exporting to XMind")
            try:
                export_to_xmind(result, str(output_path), group_by=args.group_by)
                print(f"  (Organized by: {args.group_by})")
            except Exception as e:
                logger.error(f"Failed to export to XMind: {e}")
                print(f"Error: Failed to export to XMind - {e}", file=sys.stderr)
                return 1
                
        elif args.format == 'notion':
            logger.info("Exporting to Notion-compatible Markdown")
            try:
                export_to_notion(result, str(output_path), group_by=args.group_by)
            except Exception as e:
                logger.error(f"Failed to export to Notion format: {e}")
                print(f"Error: Failed to export to Notion format - {e}", file=sys.stderr)
                return 1
        
        logger.info(f"Results written to: {args.output}")
        logger.info(f"Total highlights extracted: {result['total_highlights']}")
        
        print(f"✓ Successfully extracted {result['total_highlights']} highlights")
        print(f"✓ Results saved to: {args.output}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"Error: File not found - {e}", file=sys.stderr)
        return 1
        
    except PermissionError as e:
        logger.error(f"Permission denied: {e}")
        print(f"Error: Permission denied - {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"Error: An unexpected error occurred - {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
