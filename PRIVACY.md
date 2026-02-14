# Privacy

resumake can optionally use external AI services. This document explains what data is sent and when.

## Commands That Send Data

The following commands send your CV data to an external LLM API (Anthropic Claude, OpenAI, or any OpenAI-compatible provider):

| Command | Data Sent | When |
| --- | --- | --- |
| `resumake build` (with `--lang` other than `en`) | Full CV YAML | Only when translating (not when using cache) |
| `resumake tailor` | Full CV YAML + job description file | Always |
| `resumake bio` | Full CV YAML | Only when AI is available |
| `resumake cover` | Full CV YAML + job description file | Always |

## Commands That Never Send Data

| Command | Notes |
| --- | --- |
| `resumake build --lang en` | English-only builds are fully offline |
| `resumake validate` | Local schema validation only |
| `resumake init` | Local file scaffolding only |
| `resumake bio` (without AI) | Falls back to deterministic selection |
| `resumake export` | Local format conversion only |
| `resumake preview` | Local HTML generation only |
| `resumake diff` | Local YAML comparison only |
| `resumake themes` | Lists built-in themes only |

## How to Stay Offline

- Install without AI extras: `uv tool install resumakeai`
- Do not set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Use `--lang en` to skip translation
- Translation results are cached locally per language — subsequent builds reuse the cache without API calls

## Data Storage

- Your CV data stays on your machine (in `cv.yaml` and `output/`)
- Translation caches are stored locally in `output/.cv_<lang>_cache.yaml`
- No data is logged, stored, or shared by resumake itself
- API providers have their own data policies:
  - [Anthropic privacy policy](https://www.anthropic.com/privacy)
  - [OpenAI privacy policy](https://openai.com/policies/privacy-policy)
