"""FastAPI backend that wraps the resumake CLI tool's Python functions to provide a web API.

Endpoints:
    GET  /api/cv                  Load cv.yaml as JSON
    POST /api/cv                  Save CV data (JSON → YAML)
    GET  /api/preview             HTML preview (query: theme, lang)
    GET  /api/themes              List built-in themes with configs
    POST /api/build               Build DOCX, return filename & size
    GET  /api/download/{fn}       Download a generated file from output/
    POST /api/validate            Validate CV data against schema
    POST /api/export              Export CV to md/html/json/txt
    POST /api/upload-photo        Upload a profile photo to assets/
    GET  /api/assets/{fn}         Serve a file from assets/ (e.g. photos)
    POST /api/init                Initialize project (copy example template)
    GET  /api/status              Project status
    POST /api/tailor              Tailor CV for a job description (JSON)
    POST /api/tailor/build        Tailor + build DOCX
    POST /api/cover-letter        Generate cover letter (JSON)
    POST /api/cover-letter/build  Generate + build cover letter DOCX
    POST /api/ats                 ATS keyword analysis
    POST /api/suggest             AI improvement suggestions
    POST /api/bio                 Generate bio data (JSON)
    POST /api/bio/build           Generate + build bio DOCX
    POST /api/import              Import from JSON Resume or LinkedIn PDF
    GET  /api/settings             Get LLM provider settings (masked keys)
    POST /api/settings             Save LLM provider API keys to .env

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


class _CleanDumper(yaml.Dumper):
    """YAML Dumper subclass that preserves key order and uses block scalars."""


_CleanDumper.add_representer(str, _str_representer)


def _get_yaml_dumper() -> type:
    """Return a YAML Dumper that preserves key order and uses block scalars."""
    return _CleanDumper


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


def _load_tailor():
    from resumake.tailor import tailor_cv

    return tailor_cv


def _load_cover_letter():
    from resumake.cover_letter import _build_cover_letter_docx, _generate_cover_letter

    return _generate_cover_letter, _build_cover_letter_docx


def _load_ats():
    from resumake.ats_cmd import analyze_ats_match

    return analyze_ats_match


def _load_suggest():
    from resumake.suggest_cmd import suggest_improvements

    return suggest_improvements


def _load_bio():
    from resumake.bio import build_bio_docx, select_bio_content

    return select_bio_content, build_bio_docx


def _load_import_helpers():
    from resumake.jsonresume import json_resume_to_cv

    return json_resume_to_cv


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


class JobDescriptionRequest(BaseModel):
    job_description: str
    lang: str = "en"
    theme: Optional[str] = None


class ImportRequest(BaseModel):
    format: str  # "jsonresume" | "linkedin"


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


class BuildRequest(BaseModel):
    theme: Optional[str] = None
    lang: str = "en"


@app.post("/api/build")
def build(request: BuildRequest = BuildRequest()):
    """Build a DOCX file and return its filename and size."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        build_docx = _load_docx_builder()
        _, _, load_theme = _load_theme_module()

        cv = load_cv(DEFAULT_YAML)
        theme_obj = load_theme(request.theme) if request.theme else load_theme()
        output_path = build_docx(cv, request.lang, theme=theme_obj)

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
                errors.append(
                    {
                        "field": " → ".join(str(loc) for loc in err.get("loc", [])),
                        "message": err.get("msg", str(err)),
                        "type": err.get("type", ""),
                    }
                )
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

        max_size = 5 * 1024 * 1024  # 5MB
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="Photo must be smaller than 5MB.")

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
            "message": "Photo uploaded and cv.yaml updated.",
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


@app.get("/api/assets/{filename:path}")
def serve_asset(filename: str):
    """Serve a file from the project's assets/ directory (e.g. profile photos)."""
    try:
        _, _, ASSETS_DIR = _load_path_constants()
        file_path = (ASSETS_DIR / filename).resolve()

        if not str(file_path).startswith(str(ASSETS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied.")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Asset not found: {filename}")

        return FileResponse(path=str(file_path))
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
                part.startswith(".") or part == "__pycache__" or part == "node_modules" for part in p.parts
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
# AI-powered endpoints
# ---------------------------------------------------------------------------


@app.post("/api/tailor")
def tailor_cv_endpoint(request: JobDescriptionRequest):
    """Tailor the CV for a specific job description. Returns tailored CV as JSON."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        tailor_cv = _load_tailor()

        cv = load_cv(DEFAULT_YAML, validate=False)
        tailored = tailor_cv(cv, request.job_description)
        return JSONResponse(content=tailored)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/tailor/build")
def tailor_build_endpoint(request: JobDescriptionRequest):
    """Tailor CV and build a DOCX. Returns filename and download link."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        tailor_cv = _load_tailor()
        build_docx = _load_docx_builder()
        _, _, load_theme = _load_theme_module()

        cv = load_cv(DEFAULT_YAML, validate=False)
        tailored = tailor_cv(cv, request.job_description)
        theme_obj = load_theme(request.theme) if request.theme else load_theme()
        output_path = build_docx(tailored, request.lang, theme=theme_obj)

        return {"filename": output_path.name, "download": f"/api/download/{output_path.name}"}
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/cover-letter")
def cover_letter_endpoint(request: JobDescriptionRequest):
    """Generate a cover letter. Returns letter data as JSON."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        generate_cover_letter, _ = _load_cover_letter()

        cv = load_cv(DEFAULT_YAML, validate=False)
        letter = generate_cover_letter(cv, request.job_description, lang=request.lang)
        return JSONResponse(content=letter)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/cover-letter/build")
def cover_letter_build_endpoint(request: JobDescriptionRequest):
    """Generate a cover letter and build a DOCX. Returns filename and download link."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        generate_cover_letter, build_cover_docx = _load_cover_letter()
        _, _, load_theme = _load_theme_module()

        cv = load_cv(DEFAULT_YAML, validate=False)
        letter = generate_cover_letter(cv, request.job_description, lang=request.lang)
        theme_obj = load_theme(request.theme) if request.theme else load_theme()
        output_path = build_cover_docx(cv, letter, request.lang, theme_obj)

        return {"filename": output_path.name, "download": f"/api/download/{output_path.name}"}
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/ats")
def ats_endpoint(request: JobDescriptionRequest):
    """Analyze ATS keyword match between CV and job description."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        analyze_ats = _load_ats()

        cv = load_cv(DEFAULT_YAML, validate=False)
        result = analyze_ats(cv, request.job_description)
        return JSONResponse(content=result)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/suggest")
def suggest_endpoint():
    """Get AI-powered improvement suggestions for the current CV."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        suggest_improvements = _load_suggest()

        cv = load_cv(DEFAULT_YAML, validate=False)
        result = suggest_improvements(cv)
        return JSONResponse(content=result)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/bio")
def bio_endpoint():
    """Generate a one-pager bio from the current CV. Returns bio data as JSON."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        select_bio_content, _ = _load_bio()

        cv = load_cv(DEFAULT_YAML, validate=False)
        bio_data = select_bio_content(cv)
        return JSONResponse(content=bio_data)
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/bio/build")
def bio_build_endpoint(request: BuildRequest = BuildRequest()):
    """Generate a bio and build a DOCX. Returns filename and download link."""
    try:
        DEFAULT_YAML, load_cv = _load_cv_module()
        select_bio_content, build_bio = _load_bio()
        _, _, load_theme = _load_theme_module()

        cv = load_cv(DEFAULT_YAML, validate=False)
        bio_data = select_bio_content(cv)
        theme_obj = load_theme(request.theme) if request.theme else load_theme()
        output_path = build_bio(bio_data, request.lang, theme=theme_obj)

        return {"filename": output_path.name, "download": f"/api/download/{output_path.name}"}
    except SystemExit:
        raise HTTPException(status_code=404, detail="cv.yaml not found.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/import")
async def import_cv_endpoint(file: UploadFile = File(...), fmt: str = "jsonresume"):
    """Import a CV from an external format (JSON Resume or LinkedIn PDF)."""
    if fmt not in ("jsonresume", "linkedin"):
        raise HTTPException(status_code=400, detail="Format must be 'jsonresume' or 'linkedin'.")

    try:
        DEFAULT_YAML, _ = _load_cv_module()
        _, OUTPUT_DIR, _ = _load_path_constants()
        content = await file.read()

        if fmt == "jsonresume":
            json_resume_to_cv = _load_import_helpers()
            data = json.loads(content.decode("utf-8"))
            cv = json_resume_to_cv(data)
        else:
            # LinkedIn PDF — write temp file, import, clean up
            import tempfile

            from resumake.linkedin import import_linkedin

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            try:
                cv = import_linkedin(tmp_path)
            finally:
                tmp_path.unlink(missing_ok=True)

        # Write cv.yaml
        yaml_text = _dump_yaml(cv)
        DEFAULT_YAML.write_text(yaml_text, encoding="utf-8")

        return {"status": "ok", "message": f"Imported from {fmt}.", "cv": cv}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Settings endpoints – manage LLM provider API keys
# ---------------------------------------------------------------------------

# Keys that can be managed via the settings UI
_SETTINGS_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
]


def _mask_key(value: str) -> str:
    """Return a masked version of an API key, showing only first 4 and last 4 chars."""
    if not value:
        return ""
    if len(value) <= 12:
        return value[:3] + "..." + value[-2:]
    return value[:4] + "..." + value[-4:]


def _dotenv_path() -> Path:
    """Return the path to the project's .env file."""
    return Path.cwd() / ".env"


def _load_dotenv_dict() -> dict[str, str]:
    """Parse the project .env file into a dict. Returns {} if missing."""
    env_file = _dotenv_path()
    if not env_file.exists():
        return {}
    result = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("\"'")
        result[key] = value
    return result


def _save_dotenv_dict(data: dict[str, str]) -> None:
    """Write settings back to the project .env file, preserving unrelated lines."""
    env_file = _dotenv_path()
    existing_lines: list[str] = []
    written_keys: set[str] = set()

    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in _SETTINGS_KEYS:
                    # Replace with new value if present, or skip if cleared
                    if key in data and data[key]:
                        existing_lines.append(f"{key}={data[key]}")
                    written_keys.add(key)
                    continue
            existing_lines.append(line)

    # Append any new keys not already in the file
    for key in _SETTINGS_KEYS:
        if key not in written_keys and key in data and data[key]:
            existing_lines.append(f"{key}={data[key]}")

    env_file.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")


class SettingsRequest(BaseModel):
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: Optional[str] = None


@app.get("/api/settings")
def get_settings():
    """Return current LLM provider settings with masked API keys."""
    dotenv = _load_dotenv_dict()

    def _resolve(key: str) -> str:
        """Return value from .env, falling back to os.environ."""
        return dotenv.get(key) or os.environ.get(key, "")

    anthropic_key = _resolve("ANTHROPIC_API_KEY")
    openai_key = _resolve("OPENAI_API_KEY")
    openai_base_url = _resolve("OPENAI_BASE_URL")
    openai_model = _resolve("OPENAI_MODEL")

    return {
        "anthropic_api_key": _mask_key(anthropic_key),
        "anthropic_configured": bool(anthropic_key),
        "openai_api_key": _mask_key(openai_key),
        "openai_configured": bool(openai_key),
        "openai_base_url": openai_base_url,
        "openai_model": openai_model or "gpt-4o",
        "active_provider": "anthropic" if anthropic_key else ("openai" if openai_key else None),
    }


@app.post("/api/settings")
def save_settings(request: SettingsRequest):
    """Save LLM provider settings to the project .env file."""
    dotenv = _load_dotenv_dict()

    # Only update keys that were explicitly sent (non-None).
    # An empty string means "clear this key".
    if request.anthropic_api_key is not None:
        val = request.anthropic_api_key.strip()
        if val:
            dotenv["ANTHROPIC_API_KEY"] = val
            os.environ["ANTHROPIC_API_KEY"] = val
        else:
            dotenv.pop("ANTHROPIC_API_KEY", None)
            os.environ.pop("ANTHROPIC_API_KEY", None)

    if request.openai_api_key is not None:
        val = request.openai_api_key.strip()
        if val:
            dotenv["OPENAI_API_KEY"] = val
            os.environ["OPENAI_API_KEY"] = val
        else:
            dotenv.pop("OPENAI_API_KEY", None)
            os.environ.pop("OPENAI_API_KEY", None)

    if request.openai_base_url is not None:
        val = request.openai_base_url.strip()
        if val:
            dotenv["OPENAI_BASE_URL"] = val
            os.environ["OPENAI_BASE_URL"] = val
        else:
            dotenv.pop("OPENAI_BASE_URL", None)
            os.environ.pop("OPENAI_BASE_URL", None)

    if request.openai_model is not None:
        val = request.openai_model.strip()
        if val:
            dotenv["OPENAI_MODEL"] = val
            os.environ["OPENAI_MODEL"] = val
        else:
            dotenv.pop("OPENAI_MODEL", None)
            os.environ.pop("OPENAI_MODEL", None)

    _save_dotenv_dict(dotenv)

    # Return updated (masked) settings
    return get_settings()


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
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    # Resolve the project directory BEFORE importing resumake
    project_dir = Path(args.project).resolve()
    if not project_dir.is_dir():
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created project directory: {project_dir}")

    # Remember the resumake repo root (where web/ lives) so it stays on sys.path
    repo_root = Path(__file__).resolve().parent.parent
    import sys

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    os.chdir(project_dir)
    url = f"http://{args.host}:{args.port}"
    print(f"Project directory: {project_dir}")
    print(f"Starting server at {url}")
    print(f"API docs at {url}/api/docs")

    if not args.no_open:
        import threading
        import webbrowser

        threading.Timer(1.0, webbrowser.open, args=[url]).start()

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()
