# resumake

Build styled CV documents from a single YAML source.

`resumake` turns a `cv.yaml` file into polished Word (.docx) documents with a two-column layout, photo, icons, and consistent theming. Optionally translate to German, tailor for specific jobs, or generate a condensed one-pager bio — all from the command line.

## Features

- **YAML-first** — single source of truth for your CV data
- **Styled Word output** — two-column layout with sidebar, photo, icons, and professional typography
- **Themes** — built-in themes (classic, minimal, modern) or create your own
- **Multilingual** — generate English and German versions (AI-powered translation)
- **Tailor** — reorder and emphasize experience for a specific job description
- **Bio** — generate a condensed one-pager bio document
- **Validate** — check your YAML against the schema before building
- **Watch mode** — auto-rebuild on file changes
- **PDF export** — convert generated documents to PDF

## Quickstart

```bash
# Install
uv tool install resumake

# Scaffold a new project
resumake init my-cv
cd my-cv

# Edit cv.yaml with your information, then build
resumake build
```

## Installation

```bash
# Core (YAML → Word)
uv tool install resumake

# With AI features (translation, tailoring, bio generation)
uv tool install resumake --with anthropic

# With everything
uv tool install resumake[all]
```

Or with pip:

```bash
pip install resumake        # Core
pip install resumake[ai]    # + AI features
pip install resumake[all]   # Everything
```

## Commands

### `resumake build`

Build CV documents from YAML source.

```bash
resumake build                        # English + German (both)
resumake build --lang en              # English only
resumake build --theme minimal        # Use minimal theme
resumake build --pdf                  # Also generate PDF
resumake build --watch                # Auto-rebuild on changes
resumake build --retranslate          # Force fresh translation
```

### `resumake tailor`

Produce a tailored CV variant for a specific job description. Requires `resumake[ai]`.

```bash
resumake tailor job-description.txt
resumake tailor job-description.txt --lang de --pdf
```

### `resumake bio`

Generate a condensed one-pager bio document.

```bash
resumake bio                          # Uses AI if available, else deterministic
resumake bio --lang de --pdf
```

### `resumake validate`

Check your CV YAML against the schema.

```bash
resumake validate
resumake validate --source path/to/cv.yaml
```

### `resumake init`

Scaffold a new resumake project with an example CV and icons.

```bash
resumake init                         # In current directory
resumake init my-cv                   # In a new directory
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

skills:
  leadership: ["Team Leadership", "Agile Coaching"]
  technical: ["Python", "TypeScript", "React"]
  languages:
    - name: "English"
      level: "fluent"

profile: >
  Senior Software Engineer with 8+ years of experience...

experience:
  - title: "Senior Software Engineer"
    org: "TechCorp GmbH"
    start: "March 2021"
    end: "Present"
    bullets:
      - "Architected a microservices migration reducing deployment time by 60%"
    tech_stack: ["Python", "FastAPI", "PostgreSQL"]

education:
  - degree: "M.Sc. Computer Science"
    institution: "Technical University of Berlin"
    start: "2014"
    end: "2016"
```

Run `resumake init` to get a complete example with all supported fields.

## Themes

resumake ships with three built-in themes:

| Theme | Description |
|-------|-------------|
| `classic` | Navy sidebar, teal accents (default) |
| `minimal` | Grayscale, clean lines |
| `modern` | Dark purple sidebar, red accents |

```bash
resumake build --theme modern
```

### Custom themes

Create a `theme.yaml` in your project directory (auto-detected) or pass a path:

```yaml
name: my-theme
colors:
  primary: "1A1A2E"
  accent: "E94560"
  text_light: "EAEAEA"
  text_muted: "9A9ABF"
  text_body: "1A1A2E"
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

AI features (translation, tailoring, bio generation) require the `anthropic` package and an API key:

```bash
uv tool install resumake --with anthropic
export ANTHROPIC_API_KEY=your-key-here
```

- **Translation** caches results — re-runs are free unless you pass `--retranslate`
- **Bio** falls back to deterministic selection when no AI is available
- **Tailor** requires AI (it needs to understand the job description)

## License

MIT
