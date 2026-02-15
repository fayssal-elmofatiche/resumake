"""Live preview server — HTTP server with SSE auto-reload on file changes."""

import http.server
import threading
import time
from pathlib import Path

from .console import console, err_console
from .html_builder import build_html
from .theme import load_theme
from .utils import load_cv

# Shared state for SSE reload notifications
_reload_event = threading.Event()


class LiveReloadHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler serving the CV preview with SSE reload support."""

    source: Path
    theme_name: str | None = None

    def do_GET(self):
        if self.path == "/events":
            self._handle_sse()
        else:
            self._handle_page()

    def _handle_page(self):
        try:
            cv = load_cv(self.source)
            theme = load_theme(self.theme_name)
            html = build_html(cv, "en", theme=theme)
            # Inject SSE reload script
            reload_script = """
<script>
const evtSource = new EventSource('/events');
evtSource.onmessage = function(event) {
  if (event.data === 'reload') { location.reload(); }
};
</script>
"""
            html = html.replace("</body>", f"{reload_script}</body>")
        except Exception as e:
            html = f"<html><body><h1>Build Error</h1><pre>{e}</pre></body></html>"

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _handle_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            while True:
                if _reload_event.wait(timeout=1):
                    _reload_event.clear()
                    self.wfile.write(b"data: reload\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, format, *args):
        pass  # Suppress default logging


def start_live_server(source: Path, theme_name: str | None = None, port: int = 8642):
    """Start a live-reloading preview server."""
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        err_console.print("[red]Error:[/] 'watchdog' package required for --live preview.")
        err_console.print("Install with: [bold]uv tool install resumakeai --with watchdog[/]")
        raise SystemExit(1)

    # Configure the handler class
    LiveReloadHandler.source = source
    LiveReloadHandler.theme_name = theme_name

    class FileChangeHandler(FileSystemEventHandler):
        def __init__(self):
            self._last_trigger = 0

        def on_modified(self, event):
            if event.is_directory:
                return
            if Path(event.src_path).resolve() != source.resolve():
                return
            now = time.time()
            if now - self._last_trigger < 0.5:
                return
            self._last_trigger = now
            console.print(f"[dim]--- {source.name} changed, reloading... ---[/]")
            _reload_event.set()

    observer = Observer()
    observer.schedule(FileChangeHandler(), str(source.parent), recursive=False)
    observer.start()

    server = http.server.HTTPServer(("localhost", port), LiveReloadHandler)
    console.print(f"Live preview: [cyan]http://localhost:{port}[/]")
    console.print(f"Watching [cyan]{source}[/] for changes. Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped live preview.[/]")
    finally:
        observer.stop()
        observer.join()
        server.server_close()
