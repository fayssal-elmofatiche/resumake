# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in resumake, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email the maintainer directly at the address listed in `pyproject.toml`
3. Include a description of the vulnerability and steps to reproduce

You should receive a response within 48 hours.

## Scope

resumake handles sensitive personal data (CV content) and optionally sends it to external LLM APIs. Security-relevant areas include:

- **API key handling** — keys are read from environment variables only, never stored or logged
- **Data transmission** — see [PRIVACY.md](PRIVACY.md) for which commands send data and when
- **YAML parsing** — uses `yaml.safe_load()` exclusively (no arbitrary code execution)
- **File system access** — reads/writes only within the user's project directory and `output/`

## Supported Versions

Only the latest release is actively maintained. Update to the newest version for security fixes.
