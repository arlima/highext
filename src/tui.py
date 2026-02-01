from pathlib import Path
from typing import Iterable, Any
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, DirectoryTree, Footer, Header, Input, Label, Log, Checkbox, Static, Markdown, RadioSet, RadioButton
from textual.binding import Binding
from textual import on
import os
import logging
from datetime import datetime

from .extractor import extract_highlights_from_pdf
from .utils import format_json_output, rgb_to_hex
from .xmind_exporter import export_to_xmind
from .notion_exporter import export_to_notion, NotionExporter

class EscapableInput(Input):
    """Input widget that loses focus when Escape is pressed."""
    
    BINDINGS = [
        Binding("escape", "blur", "Blur Input"),
    ]
    
    def action_blur(self) -> None:
        self.screen.set_focus(None)

def generate_tui_preview(data: dict[str, Any], group_by: str) -> str:
    """Generate Rich-markup text for TUI preview."""
    lines = []
    
    # Title
    source_path = data.get('source_path', 'Unknown PDF')
    filename = Path(source_path).stem if source_path != 'Unknown PDF' else source_path
    lines.append(f"[bold underline]{filename}[/]\n")
    
    # Metadata
    lines.append("[bold]Document Information[/]")
    lines.append(f"- [bold]Source:[/]: {source_path}")
    lines.append(f"- [bold]Total Pages:[/] {data.get('total_pages', 'N/A')}")
    lines.append(f"- [bold]Total Highlights:[/] {data.get('total_highlights', 0)}")
    lines.append(f"- [bold]Extraction Date:[/] {data.get('extraction_date', 'N/A')}\n")
    
    # Highlights
    highlights = data.get('highlights', [])
    
    if not highlights:
        lines.append("[italic]No highlights found in this document.[/]\n")
        return "\n".join(lines)
    
    lines.append("[bold]Highlights[/]\n")

    if group_by == "page":
        # Group by page
        pages = {}
        for highlight in highlights:
            page_num = highlight.get('page', 0)
            if page_num not in pages:
                pages[page_num] = []
            pages[page_num].append(highlight)
        
        for page_num in sorted(pages.keys()):
            page_highlights = pages[page_num]
            lines.append(f"[bold]Page {page_num}[/]")
            
            # Group by color within page
            colors = {}
            for highlight in page_highlights:
                color_name = highlight.get('color_name', 'unknown')
                if color_name not in colors:
                    colors[color_name] = []
                colors[color_name].append(highlight)
            
            for color_name in sorted(colors.keys()):
                color_highlights = colors[color_name]
                lines.append(f"  [bold]{color_name.title()}[/]")
                for highlight in color_highlights:
                    text = highlight.get('text', 'No text')
                    color = highlight.get('color', [])
                    hex_color = rgb_to_hex(color)
                    
                    # Rich markup for color
                    lines.append(f"    [{hex_color}]{text}[/{hex_color}]\n")
    
    else: # group_by == "color"
        # Group by color
        colors = {}
        for highlight in highlights:
            color_name = highlight.get('color_name', 'unknown')
            if color_name not in colors:
                colors[color_name] = []
            colors[color_name].append(highlight)

        for color_name in sorted(colors.keys()):
            color_highlights = colors[color_name]
            lines.append(f"[bold]{color_name.title()}[/]")

            pages = {}
            for highlight in color_highlights:
                page_num = highlight.get('page', 0)
                if page_num not in pages:
                    pages[page_num] = []
                pages[page_num].append(highlight)

            for page_num in sorted(pages.keys()):
                page_highlights = pages[page_num]
                lines.append(f"  [bold]Page {page_num}[/]")
                for highlight in page_highlights:
                    text = highlight.get('text', 'No text')
                    color = highlight.get('color', [])
                    hex_color = rgb_to_hex(color)
                    
                    # Rich markup for color
                    lines.append(f"    [{hex_color}]{text}[/{hex_color}]\n")
    
    return "\n".join(lines)


class FilteredDirectoryTree(DirectoryTree):
    def _load_directory(self, node: Any) -> None:
        res = super()._load_directory(node)
        
        if node.children:
            # Find ".." and move to top
            target_index = -1
            for index, child in enumerate(node.children):
                if str(child.label) == "..":
                    target_index = index
                    break
            
            if target_index > 0:
                child = node.children.pop(target_index)
                node.children.insert(0, child)
        
        return res

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        import inspect
        is_root = False
        
        # Check stack to see if we are loading the root directory
        frame = inspect.currentframe()
        try:
            caller = frame.f_back
            while caller:
                if caller.f_code.co_name == '_load_directory':
                    # Check for 'node' argument first (modern Textual)
                    node_arg = caller.f_locals.get('node')
                    if node_arg and hasattr(node_arg, 'data') and hasattr(node_arg.data, 'path'):
                         path_obj = node_arg.data.path
                         if path_obj and hasattr(path_obj, 'absolute'):
                            if path_obj.absolute() == self.path.absolute():
                                is_root = True
                    
                    # Fallback check for 'path' argument (older Textual or if signature differs)
                    if not is_root:
                        path_arg = caller.f_locals.get('path')
                        if path_arg and hasattr(path_arg, 'absolute'):
                            if path_arg.absolute() == self.path.absolute():
                                is_root = True
                    
                    break
                caller = caller.f_back
        except Exception:
            pass
        finally:
            del frame

        paths_list = list(paths)
        if is_root:
            paths_list.insert(0, self.path / "..")
                
        return [
            path for path in paths_list 
            if (path.name == ".." or not path.name.startswith(".")) and (path.is_dir() or path.suffix.lower() == ".pdf")
        ]

class PDFExtractorApp(App):
    """Textual TUI for Highext."""
    
    TITLE = "Highext"

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 1fr 2fr;
    }
    
    #left-pane {
        height: 100%;
        border-right: solid $accent;
    }
    
    #middle-pane {
        height: 100%;
        border-right: solid $accent;
        padding: 1;
    }

    #right-pane {
        height: 100%;
        padding: 1;
        overflow-y: scroll;
    }
    
    .box {
        height: auto;
        border: solid $secondary;
        margin-bottom: 1;
        padding: 1;
    }
    
    #file-tree {
        height: 100%;
    }
    
    Label {
        margin-bottom: 1;
        text-style: bold;
    }
    
    Button {
        width: 100%;
        margin-top: 1;
    }
    
    Log {
        height: 1fr;
        border: solid $accent;
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_tree", "Refresh Files"),
    ]

    def __init__(self):
        super().__init__()
        self.selected_file: Path | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        
        # Left Pane: File Browser
        with Vertical(id="left-pane"):
            yield Label("Select PDF File:")
            yield FilteredDirectoryTree(os.getcwd(), id="file-tree")

        # Middle Pane: Options and Logs
        with Vertical(id="middle-pane"):
            with Vertical(classes="box"):
                yield Label("Custom Output Filename:")
                yield EscapableInput(placeholder="Optional (without extension)", id="output-name")
                
                yield Label("Export types:")
                yield Checkbox("Export JSON", value=True, id="json-cb")
                yield Checkbox("Export XMind", value=False, id="xmind-cb")
                yield Checkbox("Export Notion (Markdown)", value=False, id="notion-cb")
                
                yield Label("Group By:")
                with RadioSet(id="group-by-radio"):
                    yield RadioButton("Page", value=True, id="group-page")
                    yield RadioButton("Color", id="group-color")
                
                yield Button("Extract Highlights", variant="primary", id="extract-btn", disabled=True)
            
            yield Label("Log Output")
            yield Log(id="log")

        # Right Pane: Highlights Preview
        with Vertical(id="right-pane"):
            yield Label("Highlights Preview")
            yield Static("*Select a PDF and click Extract to view highlights*", id="preview-static", markup=True)

        yield Footer()

    @on(DirectoryTree.FileSelected)
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when a file is selected in the directory tree."""
        if event.path.suffix.lower() == ".pdf":
            self.selected_file = event.path
            self.query_one("#extract-btn").disabled = False
            self.log_message(f"Selected file: {event.path.name}")
        else:
            self.selected_file = None
            self.query_one("#extract-btn").disabled = True
            self.log_message(f"Ignored non-PDF file: {event.path.name}")

    def action_refresh_tree(self) -> None:
        """Refresh the directory tree."""
        tree = self.query_one(FilteredDirectoryTree)
        tree.reload()

    def log_message(self, message: str) -> None:
        """Write a message to the on-screen log."""
        log = self.query_one(Log)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log.write_line(f"[{timestamp}] {message}")

    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        event.stop()
        tree = self.query_one(FilteredDirectoryTree)
        
        if event.path.name == "..":
            tree.path = tree.path.parent
        else:
            tree.path = event.path

    @on(Button.Pressed, "#extract-btn")
    def run_extraction(self) -> None:
        if not self.selected_file:
            self.log_message("Error: No file selected.")
            return

        json_enabled = self.query_one("#json-cb").value
        xmind_enabled = self.query_one("#xmind-cb").value
        notion_enabled = self.query_one("#notion-cb").value
        custom_name = self.query_one("#output-name").value
        group_by = "page" if self.query_one("#group-page").value else "color"

        # Only check if no export is selected AND we don't want to just preview
        # But for now, let's allow extraction just for preview even if no export is selected
        # Or better, treat "Extract Highlights" as "Extract & Preview" + "Export if selected"
        
        self.log_message(f"Starting extraction for: {self.selected_file.name}")
        
        try:
            # Extract highlights
            result = extract_highlights_from_pdf(str(self.selected_file))
            
            if result['total_highlights'] == 0:
                self.log_message("Warning: No highlights found in the PDF.")
                self.query_one("#preview-static").update("*No highlights found.*")
            else:
                self.log_message(f"Found {result['total_highlights']} highlights.")
                
                # Update Preview
                try:
                    preview_content = generate_tui_preview(result, group_by=group_by)
                    self.query_one("#preview-static").update(preview_content)
                except Exception as e:
                    self.log_message(f"Error generating preview: {e}")

            base_name = custom_name if custom_name else self.selected_file.stem

            # JSON Export
            if json_enabled:
                output_path = self.selected_file.parent / f"{base_name}.json"
                json_output = format_json_output(result, pretty=True, group_by=group_by)
                output_path.write_text(json_output, encoding='utf-8')
                self.log_message(f"✓ JSON saved to: {output_path.name}")

            # XMind Export
            if xmind_enabled:
                output_path = self.selected_file.parent / f"{base_name}.xmind"
                try:
                    export_to_xmind(result, str(output_path), group_by=group_by)
                    self.log_message(f"✓ XMind saved to: {output_path.name}")
                except Exception as e:
                    self.log_message(f"Error exporting XMind: {e}")

            # Notion Export
            if notion_enabled:
                output_path = self.selected_file.parent / f"{base_name}.md"
                try:
                    export_to_notion(result, str(output_path), group_by=group_by)
                    self.log_message(f"✓ Notion (MD) saved to: {output_path.name}")
                except Exception as e:
                    self.log_message(f"Error exporting Notion: {e}")

            self.log_message("Done!")

        except Exception as e:
            self.log_message(f"Critical Error: {str(e)}")
            self.query_one("#preview-static").update(f"Error: {str(e)}")

def main():
    app = PDFExtractorApp()
    app.run()

if __name__ == "__main__":
    main()
