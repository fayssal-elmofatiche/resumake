# Privacy

resumake can optionally use external AI services. This document explains what data is sent and when.

## Commands That Send Data

The following commands send your CV data to an external LLM API (currently Anthropic Claude):

| Command | Data Sent | When |
|---------|-----------|------|
| `resumake build` (with `--lang de` or both languages) | Full CV YAML | Only when translating to German (not when using cache) |
| `resumake tailor` | Full CV YAML + job description file | Always |
| `resumake bio` | Full CV YAML | Only when AI is available |

## Commands That Never Send Data

| Command | Notes |
|---------|-------|
| `resumake build --lang en` | English-only builds are fully offline |
| `resumake validate` | Local schema validation only |
| `resumake init` | Local file scaffolding only |
| `resumake bio` (without AI) | Falls back to deterministic selection |

## How to Stay Offline

- Install without the `[ai]` extra: `pip install resumake`
- Do not set the `ANTHROPIC_API_KEY` environment variable
- Use `--lang en` to skip translation
- Translation results are cached locally in `output/.cv_de_cache.yaml` — subsequent builds reuse the cache without API calls

## Data Storage

- Your CV data stays on your machine (in `cv.yaml` and `output/`)
- Translation cache is stored locally in `output/.cv_de_cache.yaml`
- No data is logged, stored, or shared by resumake itself
- API providers have their own data policies — see [Anthropic's privacy policy](https://www.anthropic.com/privacy)
