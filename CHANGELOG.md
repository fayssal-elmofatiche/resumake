# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

- **Publication cover images** — publications accept an optional `image` field (a filename resolved from `assets/`). The image is embedded below the entry in both Word and HTML/PDF output. Useful for book covers.

## [0.9.0] - 2026-02-16

### Added

- **Interactive web UI** — `resumake web` launches a browser-based frontend for editing cv.yaml, live preview, building documents, and managing themes.
- **Web AI tools** — tailor CV, generate cover letters, ATS keyword analysis, content suggestions, and bio generation directly from the web UI.
- **Web import** — import from JSON Resume or LinkedIn PDF via the web UI.
- **LLM settings page** — configure Anthropic and OpenAI API keys from the web UI (stored in `.env`, keys are masked in the UI).
- **Auto-open browser** — `resumake web` automatically opens the browser on start; use `--no-open` to disable.

## [0.8.0] - 2026-02-15

### Added

- **Content suggestions** — `resumake suggest` analyzes your CV via AI and suggests bullet improvements (quantify achievements, stronger action verbs, ATS readability).
- **ATS keyword optimization** — `resumake ats <job-description.txt>` reports keyword match score, matched/missing keywords, and actionable suggestions.
- **Batch tailoring** — `resumake tailor --batch <directory>/` processes all .txt/.md files in a directory, generating one tailored CV per job description.

## [0.7.0] - 2026-02-15

### Added

- **JSON Resume import/export** — `resumake export jsonresume` and `resumake import jsonresume resume.json` for interop with the jsonresume.org ecosystem.
- **LinkedIn PDF import** — `resumake import linkedin profile.pdf` extracts and structures a LinkedIn profile export into cv.yaml using AI.
- **Live web preview** — `resumake preview --live` starts an HTTP server with SSE auto-reload on cv.yaml changes.
- **Import command** — `resumake import` supports jsonresume and linkedin formats.

## [0.6.0] - 2026-02-15

### Added

- **Custom sections** — define arbitrary sections (awards, patents, projects) in cv.yaml as top-level lists. Automatically rendered in Word, HTML, Markdown, plain text, and translated.
- **HTML builder** — themed, print-optimized HTML output matching the DOCX layout. Used for `resumake export html`, `resumake preview`, and WeasyPrint PDF.
- **WeasyPrint PDF engine** — `--pdf-engine weasyprint` generates PDF directly from HTML, removing the dependency on Word/LibreOffice. Falls back to docx2pdf with `--pdf-engine auto`.
- **Template variants** — `layout_type` in themes: `two-column` (default), `single-column`, `academic` (publications first), `compact` (tighter spacing, no photo). New built-in themes: single-column, academic, compact.
- **`--pdf-engine` flag** on build — choose between `weasyprint`, `docx2pdf`, or `auto`.
- **`--theme` flag** on preview command.
- **`--live` and `--port` flags** on preview command.
- **`pdf_engine` config key** in `.resumakerc.yaml`.

### Changed

- HTML export now uses the themed HTML builder instead of simple markdown-to-HTML conversion.
- Preview command now uses the themed HTML builder with `--theme` support.

## [0.5.0] - 2026-02-14

### Added

- **Config file** — `.resumakerc.yaml` for persistent build defaults (lang, theme, pdf, open, source, watch). Supports project-level and user-level configs with CLI overrides.
- **ATS plain-text export** — `resumake export txt` generates applicant tracking system-friendly plain text with ALL CAPS section headers and no formatting.
- **Photo validation** — `resumake validate` and `resumake build` now warn about missing, unsupported, or oversized photo files referenced in cv.yaml.

### Changed

- Default build language is now English only (use `--lang en,de` for multilingual builds).
- Translation caching is now opt-in (`--cache`); builds always re-translate by default.

### Fixed

- **Profile photo not rendering on Word for Mac** — added missing `wp:effectExtent` and `dist*` attributes to inline images (required by OOXML spec, omitted by python-docx 1.2.0).
- **Duplicate cell width elements** — `set_cell_width()` now removes existing `tcW` before appending, preventing invalid XML.
- **Sidebar section titles lowercase** — "details" and "skills" labels now correctly capitalized in English.
- **Photo path resolution** — `resolve_asset()` now handles both bare filenames (`profile.jpeg`) and prefixed paths (`assets/profile.jpeg`).

## [0.4.0] - 2026-02-13

### Added

- **Theme system** — built-in themes (classic, minimal, modern) and custom theme support via YAML
- **Schema validation** — Pydantic-based validation with `resumake validate` command
- **Init command** — `resumake init` scaffolds a new project with example CV and icons
- **LLM provider abstraction** — pluggable AI backend (Anthropic Claude, OpenAI, and compatible APIs)
- **Cover letter** — `resumake cover` generates a cover letter for a job description using AI
- **Export** — `resumake export` converts CV to Markdown, HTML, or JSON
- **Preview** — `resumake preview` generates an HTML preview and opens in the browser
- **Diff** — `resumake diff` compares two CV YAML files and shows differences
- **Themes listing** — `resumake themes` lists built-in themes with color previews
- **Rich CLI output** — styled console output, spinners for API calls, summary tables
- **Clickable links** — hyperlinks in generated Word documents are now clickable
- **`--version` flag** — `resumake --version` / `resumake -V`
- **`--open/--no-open` on build** — control whether generated files auto-open
- **`--theme` flag** on build, tailor, and bio commands
- **Graceful degradation** — core build works without optional dependencies (AI, PDF, watch)
- **Error handling** — friendly error messages for missing `cv.yaml`, missing API keys, etc.

### Changed

- Output filenames are now derived from the `name` field in `cv.yaml` (no hardcoded names)
- Path resolution uses CWD (user's project dir), not the package directory
- Icons ship with the package and fall back from user's `assets/` to built-in assets
- All CLI install instructions use `uv` consistently

### Fixed

- Links in generated documents are now clickable hyperlinks (previously plain text)
