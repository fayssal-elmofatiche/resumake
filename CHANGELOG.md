# Changelog

All notable changes to this project will be documented in this file.

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
