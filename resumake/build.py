"""Build command — generate full CV documents from YAML source."""

import time
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.table import Table

from .config import load_config, resolve
from .console import console, err_console
from .docx_builder import build_docx
from .theme import load_theme
from .translate import translate_cv
from .utils import DEFAULT_YAML, convert_to_pdf, load_cv, open_file


def _print_summary(outputs: list[Path]):
    """Print a Rich summary table of generated files."""
    table = Table(title="Generated Files", show_lines=False)
    table.add_column("File", style="cyan")
    table.add_column("Size", justify="right", style="green")
    for p in outputs:
        size = p.stat().st_size
        if size > 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.1f} MB"
        elif size > 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size} B"
        table.add_row(p.name, size_str)
    console.print(table)


def build(
    lang: Annotated[
        Optional[str],
        typer.Option(help="Comma-separated language codes (e.g. en,de,fr). Defaults to EN only."),
    ] = None,
    cache: Annotated[bool, typer.Option("--cache/--no-cache", help="Use cached translations if available.")] = False,
    source: Annotated[Optional[Path], typer.Option(help="Path to source YAML.")] = None,
    pdf: Annotated[
        Optional[bool], typer.Option("--pdf/--no-pdf", help="Also generate PDF from the Word documents.")
    ] = None,
    watch: Annotated[
        Optional[bool], typer.Option("--watch/--no-watch", help="Watch source YAML for changes and auto-rebuild.")
    ] = None,
    theme: Annotated[
        Optional[str],
        typer.Option(help="Theme name (classic, minimal, modern) or path to theme.yaml."),
    ] = None,
    open: Annotated[Optional[bool], typer.Option("--open/--no-open", help="Open the generated files.")] = None,
):
    """Build full CV documents from YAML source."""
    cfg = load_config()
    lang = resolve(lang, cfg.lang, None)
    source = Path(resolve(source, cfg.source, str(DEFAULT_YAML)))
    pdf = resolve(pdf, cfg.pdf, False)
    watch = resolve(watch, cfg.watch, False)
    theme = resolve(theme, cfg.theme, None)
    open = resolve(open, cfg.open, True)

    langs = [code.strip() for code in lang.split(",")] if lang else ["en"]
    resolved_theme = load_theme(theme)

    def do_build():
        cv_en = load_cv(source)
        outputs = []
        for target_lang in langs:
            cv = cv_en
            if target_lang != "en":
                cv = translate_cv(cv_en, lang=target_lang, retranslate=not cache)
            output_path = build_docx(cv, target_lang, theme=resolved_theme)
            outputs.append(output_path)
            if pdf:
                pdf_path = convert_to_pdf(output_path)
                outputs.append(pdf_path)
        return outputs

    # Initial build
    outputs = do_build()
    _print_summary(outputs)
    if open:
        for output_path in outputs:
            open_file(output_path)

    if watch:
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except ImportError:
            err_console.print("[red]Error:[/] 'watchdog' package required for --watch.")
            err_console.print("Install with: [bold]uv tool install resumakeai --with watchdog[/]")
            raise typer.Exit(1)

        class RebuildHandler(FileSystemEventHandler):
            def __init__(self):
                self._last_build = 0

            def on_modified(self, event):
                if event.is_directory:
                    return
                if Path(event.src_path).resolve() != source.resolve():
                    return
                now = time.time()
                if now - self._last_build < 1:
                    return
                self._last_build = now
                console.print(f"\n[dim]--- {source.name} changed, rebuilding... ---[/]")
                try:
                    outs = do_build()
                    _print_summary(outs)
                except Exception as e:
                    err_console.print(f"[red]Build error:[/] {e}")

        observer = Observer()
        observer.schedule(RebuildHandler(), str(source.parent), recursive=False)
        observer.start()
        console.print(f"\nWatching [cyan]{source}[/] for changes. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            console.print("\n[dim]Stopped watching.[/]")
        observer.join()
