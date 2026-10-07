# Contributing to NCERT AI Teacher Assistant

Thanks for helping teachers spend less time on paperwork. Contributions from educators, developers, and researchers are welcome.

A few ground rules for this project:

- Generated content is a draft. Never present model output as teacher-verified or curriculum-approved.
- Do not commit student data, teacher personal data, API keys, or NCERT textbook files. The corpus is ingested locally and excluded from Git.
- Keep NCERT/CBSE claims verifiable. Do not invent page numbers, learning-outcome codes, or exam blueprints; cite current official sources in docs.
- If you are not sure whether something is accurate, mark it as unverified rather than guessing.

## Development setup

The backend is a `uv`-managed Python project. Install [uv](https://docs.astral.sh/uv/) first.

```bash
git clone https://github.com/YOUR-USERNAME/NCERT-AI-Teacher-Assistant.git
cd NCERT-AI-Teacher-Assistant/backend
uv python install 3.11
uv sync --extra dev
cp .env.example .env
```

`uv.lock` is committed. Use `uv sync --locked --extra dev` to confirm your change works against the pinned dependency set, and update the lockfile deliberately with `uv lock` when you change `pyproject.toml`.

Do not add a `requirements.txt`; dependencies live in `backend/pyproject.toml`.

## Checks before opening a pull request

Run all of these from `backend/`:

```bash
uv run --locked pytest -q
uv run --locked python -m compileall -q app scripts tests
uv run --locked ruff check app scripts tests
```

If your change affects prompts, schemas, or API routes, describe the request/response you exercised. Prefer mocked LLM calls in tests so the suite runs without API keys or network access.

## Adding a generation feature

1. Add request/response models in `app/models/schemas.py`.
2. Add a prompt in `app/services/prompt_templates.py` and register it.
3. Implement the workflow in `app/services/generation_service.py` with Pydantic validation of the model output.
4. Expose it in `app/api/routes.py`.
5. Add a smoke test that does not require a live provider.

Prompt changes should not weaken validation. If retrieved textbook passages are unavailable, prompts must instruct the model not to claim textbook verification or fabricate citations.

## Ingestion changes

`backend/scripts/scrape_ncert.py` reads book codes and chapter ranges from the official [NCERT textbook catalogue](https://ncert.nic.in/textbook.php). Keep the request delay, keep source URLs in the index output, and do not commit downloaded PDFs or extracted text. Check NCERT's current copyright notice and terms before using or redistributing textbook material.

## Reporting issues

Include the endpoint or script, a minimal request/command, the observed result, the expected result, and whether an LLM provider or indexed corpus was involved. Redact API keys and personal data.

## Pull requests

Keep changes focused and explain the teacher-facing impact. For UI or generation changes, include a sample output and note which parts you verified against an official source.

Thank you for contributing.
