"""FastAPI backend that wraps the resumake CLI tool's Python functions to provide a web API.

Endpoints:
    GET  /api/cv              Load cv.yaml as JSON
    POST /api/cv              Save CV data (JSON → YAML)
    GET  /api/preview         HTML preview (query: theme, lang)
    GET  /api/themes          List built-in themes with configs
    POST /api/build           Build DOCX, return filename & size
    GET  /api/download/{fn}   Download a generated file from output/
    POST /api/validate        Validate CV data against schema
    POST /api/export          Export CV to md/html/json/txt
    POST /api/upload-photo    Upload a profile photo to assets/
    POST /api/init            Initialize project (copy example template)
    GET  /api/status          Project status

Usage:
    python web/server.py --project /path/to/cv-project --port 3000
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

import yaml
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# YAML helpers – custom representer for clean output
# ---------------------------------------------------------------------------


def _str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Use block scalar style ('>') for long strings or strings containing newlines."""
    if "\n" in data or len(data) > 120:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def _get_yaml_dumper() -> type:
    """Return a YAML Dumper that preserves key order and uses block scalars."""
    dumper = yaml.Dumper
    dumper.add_representer(str, _str_representer)
    return dumper


def _dump_yaml(data: dict) -> str:
    """Serialize *data* to a YAML string with clean formatting."""
    return yaml.dump(
        data,
        Dumper=_get_yaml_dumper(),
        default_flow_style=False,
        sort_keys=False,
        allow_unicode=True,
        width=120,
    )


# ---------------------------------------------------------------------------
# Lazy imports – resumake modules are imported INSIDE functions so that
# ``Path.cwd()`` (captured at import time in ``resumake.utils``) reflects
# the project directory set via ``os.chdir()`` in ``main()``.
# ---------------------------------------------------------------------------


def _load_cv_module():
    from resumake.utils import DEFAULT_YAML, load_cv
    return DEFAULT_YAML, load_cv


def _load_html_builder():
    from resumake.html_builder import build_html
    return build_html


def _load_docx_builder():
    from resumake.docx_builder import build_docx
    return build_docx


def _load_theme_module():
    from resumake.theme import BUILTIN_THEMES_DIR, list_themes, load_theme
    return BUILTIN_THEMES_DIR, list_themes, load_theme


def _load_schema_module():
    from resumake.schema import validate_cv
    return validate_cv


def _load_export_functions():
    from resumake.export_cmd import _cv_to_html, _cv_to_markdown, _cv_to_plaintext
    return _cv_to_markdown, _cv_to_html, _cv_to_plaintext


def _load_init_resources():
    from resumake.utils import BUILTIN_ASSETS_DIR, PACKAGE_DIR
    TEMPLATES_DIR = PACKAGE_DIR / "templates"
    return TEMPLATES_DIR, BUILTIN_ASSETS_DIR


def _load_path_constants():
    from resumake.utils import ASSETS_DIR, DEFAULT_YAML, OUTPUT_DIR
    return DEFAULT_YAML, OUTPUT_DIR, ASSETS_DIR


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="resumake", docs_url="/api/docs", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ExportRequest(BaseModel):
    format: str  # "md" | "html" | "json" | "txt"


class BuildResponse(BaseModel):
    filename: str
    size: str


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.get("/api/cv")
def get_cv():
    """Load cv.yaml and return its contents as JSON."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        cv = load_cv(DEFAULT_YAML, validate=False)
        return JSONResponse(content=cv)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found. Run POST /api/init first.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/cv")
def save_cv(data: dict):
    """Receive CV data as JSON and write it back to cv.yaml as YAML."""
    try:
        DEFAULT_YAML, _ = _load_cv_module()

        # Ensure integers stay as integers (e.g. publication years)
        def _fix_types(obj):
            if isinstance(obj, dict):
                return {k: _fix_types(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_fix_types(v) for v in obj]
            if isinstance(obj, float) and obj == int(obj):
                return int(obj)
            return obj

        cleaned = _fix_types(data)
        yaml_text = _dump_yaml(cleaned)
        DEFAULT_YAML.write_text(yaml_text, encoding="utf-8")
        return {"status": "ok", "message": "cv.yaml saved successfully."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/preview", response_class=HTMLResponse)
def preview(
    theme: Optional[str] = Query(None, description="Theme name or path"),
    lang: str = Query("en", description="Language code"),
):
    """Return an HTML preview of the CV."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        build_html = _load_html_builder()
        _, _, load_theme = _load_theme_module()

        cv = load_cv(DEFAULT_YAML, validate=False)
        theme_obj = load_theme(theme) if theme else load_theme()
        html = build_html(cv, lang, theme=theme_obj)
        return HTMLResponse(content=html)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/themes")
def get_themes():
    """List all built-in themes with their full configuration."""
    try:
        BUILTIN_THEMES_DIR, list_themes, _ = _load_theme_module()

        themes = []
        for name in list_themes():
            theme_path = BUILTIN_THEMES_DIR / f"{name}.yaml"
            if theme_path.exists():
                with open(theme_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                config.setdefault("name", name)
                themes.append(config)
        return themes
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/build")
def build():
    """Build a DOCX file and return its filename and size."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        build_docx = _load_docx_builder()

        cv = load_cv(DEFAULT_YAML)
        output_path = build_docx(cv, "en")

        size_bytes = output_path.stat().st_size
        if size_bytes >= 1_048_576:
            size_str = f"{size_bytes / 1_048_576:.1f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes} B"

        return BuildResponse(filename=output_path.name, size=size_str)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/download/{filename:path}")
def download(filename: str):
    """Download a generated file from the output/ directory."""
    try:
        _, OUTPUT_DIR, _ = _load_path_constants()
        file_path = (OUTPUT_DIR / filename).resolve()

        # Security: ensure the resolved path is inside output/
        if not str(file_path).startswith(str(OUTPUT_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied.")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")

        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/validate")
def validate_cv_endpoint(data: dict):
    """Validate CV data against the Pydantic schema."""
    try:
        validate_cv = _load_schema_module()
        validate_cv(data)
        return {"valid": True, "errors": []}
    except Exception as exc:
        # Pydantic ValidationError has a .errors() method
        errors = []
        if hasattr(exc, "errors"):
            for err in exc.errors():
                errors.append({
                    "field": " → ".join(str(loc) for loc in err.get("loc", [])),
                    "message": err.get("msg", str(err)),
                    "type": err.get("type", ""),
                })
        else:
            errors.append({"field": "", "message": str(exc), "type": "error"})
        return {"valid": False, "errors": errors}


@app.post("/api/export")
def export_cv(request: ExportRequest):
    """Export CV to the requested format and return the file for download."""
    fmt = request.format.lower().lstrip(".")
    if fmt not in ("md", "markdown", "html", "json", "txt", "text"):
        raise HTTPException(
            status_code=400,
            detail=f"Unknown format '{fmt}'. Use: md, html, json, txt.",
        )

    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        _, OUTPUT_DIR, _ = _load_path_constants()
        _cv_to_markdown, _cv_to_html, _cv_to_plaintext = _load_export_functions()

        cv = load_cv(DEFAULT_YAML, validate=False)

        from resumake.utils import slugify_name
        slug = slugify_name(cv["name"])

        if fmt in ("md", "markdown"):
            content = _cv_to_markdown(cv)
            ext = "md"
        elif fmt == "html":
            build_html = _load_html_builder()
            content = build_html(cv, "en")
            ext = "html"
        elif fmt in ("txt", "text"):
            content = _cv_to_plaintext(cv)
            ext = "txt"
        else:
            content = json.dumps(cv, indent=2, ensure_ascii=False)
            ext = "json"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{slug}_CV.{ext}"
        output_path.write_text(content, encoding="utf-8")

        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type="application/octet-stream",
        )
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    """Upload a profile photo to the project's assets/ directory and update cv.yaml."""
    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".tiff", ".tif"}

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image format '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )

    try:
        _, _, ASSETS_DIR = _load_path_constants()
        DEFAULT_YAML, load_cv = _load_cv_module()

        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        dest = ASSETS_DIR / file.filename
        content = await file.read()
        dest.write_bytes(content)

        # Update cv.yaml photo field
        if DEFAULT_YAML.exists():
            cv = load_cv(DEFAULT_YAML, validate=False)
            cv["photo"] = file.filename
            yaml_text = _dump_yaml(cv)
            DEFAULT_YAML.write_text(yaml_text, encoding="utf-8")

        return {
            "status": "ok",
            "filename": file.filename,
            "path": str(dest),
            "message": f"Photo uploaded and cv.yaml updated.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/init")
def init_project():
    """Initialize a resumake project if cv.yaml doesn't exist.

    Copies the example template to cv.yaml and built-in icons to assets/.
    """
    try:
        DEFAULT_YAML, _ = _load_cv_module()
        TEMPLATES_DIR, BUILTIN_ASSETS_DIR = _load_init_resources()

        created_files = []

        # Copy example CV
        if DEFAULT_YAML.exists():
            return {
                "status": "skipped",
                "message": "cv.yaml already exists.",
                "created": [],
            }

        example_src = TEMPLATES_DIR / "cv.example.yaml"
        if not example_src.exists():
            raise HTTPException(status_code=500, detail="Example template not found in package.")

        shutil.copy2(str(example_src), str(DEFAULT_YAML))
        created_files.append("cv.yaml")

        # Copy built-in icons to assets/
        _, _, ASSETS_DIR = _load_path_constants()
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        if BUILTIN_ASSETS_DIR.exists():
            for icon in BUILTIN_ASSETS_DIR.glob("*.png"):
                dest = ASSETS_DIR / icon.name
                if not dest.exists():
                    shutil.copy2(str(icon), str(dest))
                    created_files.append(f"assets/{icon.name}")

        # Create output directory
        _, OUTPUT_DIR, _ = _load_path_constants()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Create .gitignore
        project_dir = Path.cwd()
        gitignore = project_dir / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text("output/\nassets/profile.*\n.venv/\n__pycache__/\n*.pyc\n")
            created_files.append(".gitignore")

        return {
            "status": "ok",
            "message": "Project initialized successfully.",
            "created": created_files,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/status")
def project_status():
    """Return the current project status: whether cv.yaml exists, photo, file listing."""
    try:
        DEFAULT_YAML, _, ASSETS_DIR = _load_path_constants()

        has_cv = DEFAULT_YAML.exists()

        # Check for photo in assets/
        has_photo = False
        photo_filename = None
        if has_cv:
            try:
                _, load_cv = _load_cv_module()
                cv = load_cv(DEFAULT_YAML, validate=False)
                photo_ref = cv.get("photo")
                if photo_ref:
                    photo_path = ASSETS_DIR / photo_ref
                    has_photo = photo_path.exists()
                    if has_photo:
                        photo_filename = photo_ref
            except Exception:
                pass

        # List relevant project files
        project_dir = Path.cwd()
        files = []
        for p in sorted(project_dir.rglob("*")):
            if p.is_file() and not any(
                part.startswith(".") or part == "__pycache__" or part == "node_modules"
                for part in p.parts
            ):
                try:
                    rel = p.relative_to(project_dir)
                    files.append(str(rel))
                except ValueError:
                    pass

        return {
            "has_cv": has_cv,
            "has_photo": has_photo,
            "photo": photo_filename,
            "project_dir": str(project_dir),
            "files": files[:200],  # Cap at 200 entries
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Static files – mounted LAST so API routes take priority
# ---------------------------------------------------------------------------

_static_dir = Path(__file__).parent / "static"
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")


# ---------------------------------------------------------------------------
# Main – CLI entry point
# ---------------------------------------------------------------------------


def main():
    """Parse CLI args, chdir to the project directory, then start the uvicorn server."""
    import argparse

    import uvicorn

    parser = argparse.ArgumentParser(description="resumake web server")
    parser.add_argument(
        "--project",
        default=".",
        help="Path to the resumake project directory (containing cv.yaml)",
    )
    parser.add_argument("--port", type=int, default=3000, help="Server port (default: 3000)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    args = parser.parse_args()

    # Resolve the project directory BEFORE importing resumake
    project_dir = Path(args.project).resolve()
    if not project_dir.is_dir():
        print(f"Error: project directory does not exist: {project_dir}")
        raise SystemExit(1)

    # Remember the resumake repo root (where web/ lives) so it stays on sys.path
    repo_root = Path(__file__).resolve().parent.parent
    import sys
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    os.chdir(project_dir)
    print(f"Project directory: {project_dir}")
    print(f"Starting server at http://{args.host}:{args.port}")
    print(f"API docs at http://{args.host}:{args.port}/api/docs")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
