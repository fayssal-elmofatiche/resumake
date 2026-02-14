# Contributing to resumake

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/fayssal-elmofatiche/resumake.git
cd resumake
uv sync --all-extras
```

## Running Tests

```bash
uv run pytest
```

## Linting

```bash
uv run ruff check .
uv run ruff format --check .
```

## Adding a Theme

1. Create a YAML file in `resumake/themes/`
2. Follow the structure of `classic.yaml`
3. All color values are hex strings (without `#`)
4. Test with `resumake build --theme your-theme`

## Adding an Output Format

The current architecture is built around `python-docx`. To add a new format:

1. Create a new builder module (e.g., `html_builder.py`)
2. Implement a `build_html(cv, lang, theme)` function
3. Add a `--format` option to the `build` command

## Pull Requests

- Keep PRs focused on a single change
- Add tests for new features
- Run `ruff check .` and `pytest` before submitting
