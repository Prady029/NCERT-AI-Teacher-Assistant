# NCERT AI Teacher Assistant

A teacher-facing prototype for drafting NCERT-aligned lesson plans, question papers, chapter summaries, and formative feedback. The backend combines configurable LLM providers with optional retrieval from NCERT chapter PDFs downloaded from the official catalogue.

> **Important:** Generated material is a draft, not a substitute for teacher judgment. Review factual accuracy, curriculum alignment, difficulty, accessibility, and marking before classroom use. Do not submit identifiable student information.

## Current status

The repository currently contains a **FastAPI backend prototype**. It does not yet include the full teacher dashboard, user accounts, production authentication, classroom management, or a complete curriculum corpus. The README describes the intended direction; the checklist below separates working backend pieces from planned work.

### Implemented

- FastAPI endpoints for lesson plans, question papers, summaries, formative response evaluation, health, and curriculum metadata.
- Pydantic request/response validation and structured prompts.
- Google Gemini, OpenAI, and Anthropic generation adapters (provider packages/API keys required).
- NCERT catalogue discovery and chapter-PDF download/text extraction script.
- Optional Qdrant-backed retrieval; indexing requires Google embeddings, a running Qdrant instance, and a configured indexing key.
- Sample curriculum metadata for NCERT Science Classes 9 and 10. This is reference metadata, not a substitute for the current official syllabus.

### Planned / not implemented yet

- Next.js teacher interface and authentication.
- Full NCERT/CBSE curriculum maps, textbook corpus validation, and supported-language coverage.
- Learning-outcome and exam-blueprint verification against current official documents.
- Persistent teacher feedback workflow, analytics, export, and deployment hardening.

## Repository layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # HTTP API
│   │   ├── core/config.py             # Environment-backed settings
│   │   ├── models/schemas.py          # Request/response models
│   │   └── services/                  # LLM, prompts, RAG, generation
│   ├── scripts/scrape_ncert.py        # Catalogue discovery/PDF ingestion
│   ├── tests/                         # Backend smoke tests
│   ├── pyproject.toml                 # uv-managed dependencies
│   ├── uv.lock                        # Locked dependency set
│   └── .env.example
├── data/
│   ├── curriculum/                    # Small, hand-maintained sample maps
│   └── ncert_raw/                     # Downloaded PDFs/text (not committed)
└── .github/workflows/ci.yml
```

## Setup

Install [uv](https://docs.astral.sh/uv/) and use Python 3.10+.

```bash
cd backend
uv python install 3.11
uv sync --extra dev
cp .env.example .env
```
`uv.lock` pins the resolved environment. Use `uv sync --locked --extra dev` in CI or when you want to ensure the lockfile is unchanged.

Set the provider key you plan to use in `backend/.env`. For Google generation and embeddings, set `GOOGLE_API_KEY`. The defaults do not require credentials for health/curriculum endpoints; generation will return an error until a provider key is configured.

Start the API from `backend/`:

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive API docs: <http://127.0.0.1:8000/docs>

## NCERT catalogue and chapter ingestion

The scraper reads book codes and chapter ranges from the official NCERT catalogue page instead of assuming catalogue query parameters:

```bash
# Discover the current catalogue and save its exact labels/codes
uv run python scripts/scrape_ncert.py --catalogue-json ../data/ncert_catalogue.json

# Preview books for a class (use the subject label exactly as it appears in the catalogue)
uv run python scripts/scrape_ncert.py --class 10 --subject Science

# Download chapter PDFs, extract text, and write an index
uv run python scripts/scrape_ncert.py \
  --class 10 --subject Science --book-code jesc1 --download \
  --output ../data/ncert_raw --delay 1.0
```

Source: [NCERT Textbooks PDF catalogue](https://ncert.nic.in/textbook.php). The script uses a polite delay and stores the source URL alongside each downloaded chapter. Check NCERT's current copyright notice and terms before downloading, retaining, redistributing, or using textbook material. PDFs and extracted text are excluded from Git; ingest locally and do not commit the corpus.

PDF text extraction quality varies by document; scanned/image-only pages may require OCR, which is not included yet. Verify inferred chapter titles and extracted text before indexing.

## Retrieval setup (optional)

Run Qdrant locally (example):

```bash
docker run --rm -p 6333:6333 qdrant/qdrant
```

Set `QDRANT_URL`, `GOOGLE_API_KEY`, and a long random `INDEXING_API_KEY` in `.env`. From the backend directory, index already-downloaded/extracted chapters:

```bash
curl -X POST 'http://127.0.0.1:8000/api/v1/admin/index-textbooks?subject=science&class_level=10' \
  -H 'X-Indexing-Api-Key: YOUR_INDEXING_API_KEY'
```

The indexing route is disabled unless `INDEXING_API_KEY` is configured. Do not expose this prototype directly to the public internet; deployment still needs authentication, authorization, rate limits, logging/privacy controls, and secret management.

## API examples

```bash
curl -X POST http://127.0.0.1:8000/api/v1/lesson-plans \
  -H 'Content-Type: application/json' \
  -d '{
    "subject":"science",
    "class_level":10,
    "chapter":"Light – Reflection and Refraction",
    "duration_periods":2,
    "student_profile":"mixed_ability",
    "pedagogical_model":"5e"
  }'
```

Other endpoints:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/v1/health` | API/provider readiness |
| `GET` | `/api/v1/curriculum/{subject}/{class_level}` | Locally available curriculum metadata |
| `POST` | `/api/v1/lesson-plans` | Draft a 5E lesson plan |
| `POST` | `/api/v1/question-papers` | Draft questions and marking scheme |
| `POST` | `/api/v1/chapter-summaries` | Draft a chapter summary |
| `POST` | `/api/v1/evaluate` | Formative feedback on an answer |
| `POST` | `/api/v1/admin/index-textbooks` | Protected local corpus indexing |

## Tests

```bash
cd backend
uv run pytest -q
uv run python -m compileall -q app scripts tests
```

Generation and retrieval tests should mock provider/network calls; no live API key is needed for the smoke tests.

## Curriculum accuracy and responsible use

NCERT textbook availability and syllabus content can change, including rationalised/revised material. Do not treat old chapter lists or the sample JSON files as the current CBSE assessment blueprint. Verify against current official NCERT/CBSE sources for the relevant academic year. Keep retrieved passage provenance with generated outputs as a future improvement; do not invent page references when none were retrieved.

The project is intended to support teachers. A teacher remains responsible for reviewing, adapting, and approving every generated artifact. Do not use model-generated marks as the sole basis for high-stakes grading.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). The project is licensed under the [MIT License](LICENSE); third-party NCERT content remains subject to NCERT's own terms and copyright notices.

## Author

**Pradyumna Kumar Sahoo** — [GitHub](https://github.com/Prady029) · [Portfolio](https://prady029.github.io)
