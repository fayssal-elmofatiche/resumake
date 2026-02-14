# resumake

[![CI](https://github.com/fayssal-elmofatiche/resumake/actions/workflows/ci.yml/badge.svg)](https://github.com/fayssal-elmofatiche/resumake/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Build styled CV documents from a single YAML source.

**resumake** turns a `cv.yaml` file into polished Word (.docx) documents with a two-column layout, photo, icons, and consistent theming. Translate to any language, tailor for a specific job, generate a cover letter, or export to Markdown/HTML/JSON — all from the command line.

## Quickstart

```bash
# Install
uv tool install resumakeai

# Scaffold a new project
resumake init my-cv
cd my-cv

# Edit cv.yaml with your information, then build
resumake build --lang en
```

## Installation

**With [uv](https://docs.astral.sh/uv/) (recommended):**

```bash
uv tool install resumakeai                      # Core (YAML -> Word)
uv tool install resumakeai --with anthropic     # + AI (Anthropic Claude)
uv tool install resumakeai --with openai        # + AI (OpenAI / compatible)
uv tool install "resumakeai[all]"               # Everything
```

**With pip:**

```bash
pip install resumakeai              # Core
pip install "resumakeai[anthropic]" # + Anthropic Claude
pip install "resumakeai[openai]"    # + OpenAI / compatible
pip install "resumakeai[all]"       # Everything
```

### Optional extras

| Extra | Packages | Enables |
| --- | --- | --- |
| `anthropic` | `anthropic` | AI features via Anthropic Claude |
| `openai` | `openai` | AI features via OpenAI (or any compatible API) |
| `pdf` | `docx2pdf` | PDF export via `--pdf` |
| `watch` | `watchdog` | Auto-rebuild via `--watch` |
| `all` | All of the above | Everything |

## Features

- **YAML-first** — single source of truth for all your CV data
- **Styled Word output** — two-column layout with sidebar, photo, icons, clickable links, and professional typography
- **Themes** — three built-in themes or bring your own via YAML
- **Multilingual** — translate to any language via AI, with per-language caching and auto-invalidation
- **Tailor** — reorder and emphasize experience for a specific job description
- **Cover letter** — AI-generated cover letter matched to a job description
- **Bio** — generate a condensed one-pager bio document
- **Export** — convert to Markdown, HTML, or JSON
- **Preview** — instant HTML preview in your browser
- **Diff** — compare two CV YAML files side by side
- **Validate** — check your YAML against the schema before building
- **Watch mode** — auto-rebuild on file changes
- **PDF export** — convert generated documents to PDF
- **Offline by default** — core build requires no API keys or network access

## Commands

### `resumake build`

Build CV documents from YAML source.

```bash
resumake build                        # English + German (default)
resumake build --lang en              # English only
resumake build --lang fr              # French (any language code works)
resumake build --lang en,fr,de        # Multiple languages at once
resumake build --theme minimal        # Use a different theme
resumake build --pdf                  # Also generate PDF
resumake build --no-open              # Don't auto-open the files
resumake build --watch                # Auto-rebuild on changes
resumake build --retranslate          # Force fresh translation (ignores cache)
```

### `resumake tailor`

Produce a tailored CV variant for a specific job description. Requires AI.

```bash
resumake tailor job-description.txt
resumake tailor job-description.txt --lang de --pdf
```

### `resumake cover`

Generate a cover letter matching your CV to a job description. Requires AI.

```bash
resumake cover job-description.txt
resumake cover job-description.txt --lang fr --pdf --theme modern
```

### `resumake bio`

Generate a condensed one-pager bio document.

```bash
resumake bio                          # Uses AI if available, else deterministic
resumake bio --lang de --pdf
```

### `resumake export`

Export your CV to Markdown, HTML, or JSON.

```bash
resumake export md                    # Markdown
resumake export html                  # Self-contained HTML page
resumake export json                  # Raw JSON
resumake export md -o resume.md       # Custom output path
```

### `resumake preview`

Generate an HTML preview and open it in your browser.

```bash
resumake preview
```

### `resumake diff`

Compare two CV YAML files and show what changed.

```bash
resumake diff cv.yaml cv_tailored.yaml
```

### `resumake themes`

List available built-in themes with color previews.

```bash
resumake themes
```

### `resumake validate`

Check your CV YAML against the schema.

```bash
resumake validate
```

### `resumake init`

Scaffold a new resumake project with an example CV and icons.

```bash
resumake init                         # In current directory
resumake init my-cv                   # In a new directory
```

### Global options

```bash
resumake --version                    # Show version
resumake --help                       # Show help
```

## CV YAML Structure

```yaml
name: "Jane Doe"
title: "Senior Software Engineer"
photo: "profile.jpeg"

contact:
  address: "Berlin, Germany"
  phone: "+49 123 456 7890"
  email: "jane.doe@example.com"
  nationality: "German"

links:
  - label: "LinkedIn"
    url: "https://linkedin.com/in/janedoe"
  - label: "GitHub"
    url: "https://github.com/janedoe"

skills:
  leadership: ["Team Leadership", "Agile Coaching"]
  technical: ["Python", "TypeScript", "React"]
  languages:
    - name: "English"
      level: "fluent"     # native | fluent | professional | basic

profile: >
  Senior Software Engineer with 8+ years of experience...

experience:
  - title: "Senior Software Engineer"
    org: "TechCorp GmbH"
    start: "March 2021"
    end: "Present"
    description: "Leading backend development for a SaaS platform."
    bullets:
      - "Architected a microservices migration reducing deployment time by 60%"
    tech_stack: ["Python", "FastAPI", "PostgreSQL"]

education:
  - degree: "M.Sc. Computer Science"
    institution: "Technical University of Berlin"
    start: "2014"
    end: "2016"
```

Experience entries accept arbitrary extra fields (e.g. `tech_stack`, `soft_skills`, `project_methodology`) which are rendered as labeled metadata below the bullets.

Run `resumake init` to get a complete example with all supported sections including testimonials, certifications, publications, volunteering, and references.

## Themes

resumake ships with three built-in themes:

| Theme | Sidebar | Accent | Fonts |
| --- | --- | --- | --- |
| **`classic`** (default) | Dark navy `#0F141F` | Teal `#0AA8A7` | Arial Narrow / Calibri |
| **`minimal`** | Dark gray `#2C2C2C` | Gray `#555555` | Helvetica |
| **`modern`** | Deep purple `#1A1A2E` | Red `#E94560` | Calibri |

```bash
resumake build --theme modern
resumake themes                       # List all themes with color swatches
```

### Custom themes

Create a `theme.yaml` in your project directory (auto-detected) or pass a path:

```yaml
name: my-theme
colors:
  primary: "1A1A2E"       # Sidebar background
  accent: "E94560"        # Links, dividers, labels
  text_light: "EAEAEA"    # Sidebar text
  text_muted: "9A9ABF"    # Secondary text (dates, labels)
  text_body: "1A1A2E"     # Main body text
fonts:
  heading: "Calibri"
  body: "Calibri"
layout:
  sidebar_width_cm: 5.5
  main_width_cm: 12.5
sizes:
  name_pt: 15
  heading_pt: 13
  body_pt: 9
```

## AI Features

AI-powered features work with multiple LLM providers. Install the one you prefer and set an API key:

**Anthropic Claude:**

```bash
uv tool install resumakeai --with anthropic
export ANTHROPIC_API_KEY=your-key-here
```

**OpenAI:**

```bash
uv tool install resumakeai --with openai
export OPENAI_API_KEY=your-key-here
```

**OpenAI-compatible APIs** (Ollama, LiteLLM, Azure, etc.):

```bash
export OPENAI_API_KEY=your-key
export OPENAI_BASE_URL=http://localhost:11434/v1   # e.g. Ollama
export OPENAI_MODEL=llama3                          # optional, defaults to gpt-4o
```

The provider is auto-detected from environment variables (checked in order: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`).

| Feature | Requires AI | Fallback |
| --- | --- | --- |
| Translation (`--lang <code>`) | Yes | Uses cached translation if available |
| Tailoring (`resumake tailor`) | Yes | No fallback — AI required |
| Cover letter (`resumake cover`) | Yes | No fallback — AI required |
| Bio (`resumake bio`) | Optional | Deterministic selection from CV data |

Translations are cached per language (e.g. `output/.cv_de_cache.yaml`, `output/.cv_fr_cache.yaml`). The cache auto-invalidates when your source `cv.yaml` changes, and incomplete translations are automatically detected and re-triggered.

See [PRIVACY.md](PRIVACY.md) for details on what data is sent and when.

## Development

```bash
git clone https://github.com/fayssal-elmofatiche/resumake.git
cd resumake
uv sync --all-extras
uv run pytest
uv run ruff check .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

## License

[MIT](LICENSE)
