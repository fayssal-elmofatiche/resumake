"""Tests for live preview server."""

import io
import threading

from resumake.live_server import LiveReloadHandler


class _FakeWFile(io.BytesIO):
    """Fake wfile that captures written data."""

    def flush(self):
        pass


def _make_handler(source_path, path="/"):
    """Create a LiveReloadHandler with mocked request and socket."""
    LiveReloadHandler.source = source_path
    LiveReloadHandler.theme_name = None

    class FakeRequest:
        def makefile(self, *args, **kwargs):
            return io.BytesIO()

    handler = LiveReloadHandler.__new__(LiveReloadHandler)
    handler.request = FakeRequest()
    handler.client_address = ("127.0.0.1", 0)
    handler.server = type("Server", (), {"server_name": "localhost", "server_port": 8642})()
    handler.requestline = f"GET {path} HTTP/1.1"
    handler.command = "GET"
    handler.path = path
    handler.request_version = "HTTP/1.1"
    handler.headers = {}
    handler.wfile = _FakeWFile()

    # Track response headers
    handler._response_code = None
    handler._headers = {}

    def mock_send_response(code, message=None):
        handler._response_code = code

    handler.send_response = mock_send_response

    def mock_send_header(key, value):
        handler._headers[key] = value

    handler.send_header = mock_send_header
    handler.end_headers = lambda: None

    return handler


def test_handler_serves_html(sample_cv, tmp_path):
    """Handler serves HTML for GET /."""
    import yaml

    cv_file = tmp_path / "cv.yaml"
    cv_file.write_text(yaml.dump(sample_cv))
    handler = _make_handler(cv_file, "/")
    handler._handle_page()
    output = handler.wfile.getvalue().decode()
    assert "<!DOCTYPE html>" in output
    assert "Jane Doe" in output


def test_handler_injects_sse_script(sample_cv, tmp_path):
    """Handler injects SSE reload script into HTML."""
    import yaml

    cv_file = tmp_path / "cv.yaml"
    cv_file.write_text(yaml.dump(sample_cv))
    handler = _make_handler(cv_file, "/")
    handler._handle_page()
    output = handler.wfile.getvalue().decode()
    assert "EventSource" in output
    assert "/events" in output


def test_sse_content_type(sample_cv, tmp_path):
    """GET /events returns text/event-stream content type."""
    import yaml

    cv_file = tmp_path / "cv.yaml"
    cv_file.write_text(yaml.dump(sample_cv))
    handler = _make_handler(cv_file, "/events")

    # Start SSE in a thread and cancel quickly
    from resumake.live_server import _reload_event

    _reload_event.set()

    def run_sse():
        try:
            handler._handle_sse()
        except Exception:
            pass

    t = threading.Thread(target=run_sse, daemon=True)
    t.start()
    t.join(timeout=0.5)

    assert handler._headers.get("Content-Type") == "text/event-stream"
