# Secure Clinical RAG Validator

A portfolio adaptation of a clinical-record retrieval-augmented generation (RAG) prototype. It demonstrates how a Streamlit interface, FastAPI service, PostgreSQL with pgvector, local embeddings, Presidio redaction, and NeMo Guardrails can be connected in a local Docker Compose workflow.

This is an educational software prototype. It is not clinically validated, is not intended for diagnosis or treatment decisions, and is not approved for real patient information.

## Project background

This repository is based on the project provided by my instructor, who gave permission for me to use it as a portfolio repository. The original project is available at [Secure-EHR-Insight-Clinical-Validator](https://github.com/nimowhyca/Secure-EHR-Insight-Clinical-Validator). This attribution does not grant rights to third-party data or materials excluded from this repository.

No license file is included. Do not assume that this code is available for reuse beyond the permission described above.

## Architecture

```text
Streamlit UI
  | selected patient ID and latest question
  v
FastAPI
  | local question embedding
  v
PostgreSQL + pgvector
  | up to five nearest records filtered by patient ID
  v
Presidio redaction -> NeMo Guardrails -> configured Groq-compatible LLM
  | answer and redacted retrieved snippets
  v
Streamlit response and transparency panel
```

- **Streamlit** provides the patient selector and chat interface. Its session transcript is cleared when the selected patient changes.
- **FastAPI** validates requests, retrieves context for the supplied patient filter, and sends only the latest user question and current retrieved context to Guardrails. Previous client-supplied messages are discarded.
- **PostgreSQL and pgvector** store encounter fields and perform similarity search over embeddings, limited to five candidate rows for the selected patient.
- **Sentence Transformers** uses the configured BioClinical ModernBERT embedding model locally. The latest question is embedded before it is redacted.
- **Presidio** attempts to redact configured identifiers from retrieved context and the latest question before model generation. Redaction is best effort, not a guarantee.
- **NeMo Guardrails** applies configured instructions to the language-model interaction. It cannot guarantee correct, safe, or evidence-grounded output.
- **Groq-compatible provider** generates responses from the redacted prompt. The prompt is sent to an external provider.

The chat API returns a fixed insufficient-evidence response when no retrieved rows contain displayable fields. Retrieved snippets shown in the UI are context, not independently verified citations.

## Requirements

- Docker Engine or Docker Desktop with Docker Compose v2
- A Groq API key for model responses
- Network access and disk space for image dependencies and model downloads on first startup

No host Python installation is required for the documented Docker workflow.

## Configure and start

From PowerShell in this repository:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and set a strong, unique `DB_PASSWORD` and your provider key in `OPENAI_API_KEY`. The latter variable name is retained by the application configuration although the configured endpoint is Groq-compatible. Never commit `.env` or share its values.

Start the services:

```powershell
docker compose up --build
```

Open:

- Streamlit: <http://localhost:8501>
- FastAPI docs: <http://localhost:8000/docs>

Compose binds the service ports to loopback for local development. This is not authentication or patient authorization. Do not expose the services to a network without a separately reviewed access-control and deployment design.

## Data prerequisites

The clinical dataset is **not included**. The ingestion script expects a locally available CSV at `data/MIMIC_IV_Trasncript.csv` with columns compatible with `src/database/schema.sql`. Do not put real patient information in this public repository, screenshots, test fixtures, prompts, or logs.

Use only data you are independently authorized to access and process. MIMIC-IV access is governed by [PhysioNet's MIMIC-IV page and terms](https://physionet.org/content/mimiciv/3.1/), including credentialing and data-use requirements. This repository does not grant data access or redistribution rights.

The Kaggle listing used as a project reference was published by Isaac Ritharson: [MIMIC-IV cleaned medical transcripts](https://www.kaggle.com/datasets/isaacritharson/mimic-iv-cleaned-medical-transcripts). Kaggle metadata lists an MIT license and identifies MIMIC-IV as its source. That listing is attribution, not verification that underlying MIMIC-derived material may be redistributed under those terms. The CSV is not included; verify all applicable source-data terms before obtaining or using any copy.

The ingestion script expects that specific transformed CSV and there is no converter from the original PhysioNet release in this repository. After arranging a compatible dataset you are authorized to use, create the `data` directory and place the file there. The directory is mounted read-only into the app container. On a fresh database, run these commands once and in order:

```powershell
docker compose exec app python scripts/01_ingest_baseline_data.py
docker compose exec app python scripts/02_verify_ingestion.py
docker compose exec app python scripts/03_apply_vector_schema.py
docker compose exec app python scripts/04_generate_embeddings.py
docker compose exec app python scripts/05_test_vector_search.py
```

Ingestion appends records and is not idempotent; repeating it can create duplicates. Embedding generation processes up to 100 unembedded rows per run. The database volume persists across normal restarts. Do not remove it if you need to preserve local database contents.

## Tests

Run the unit tests in the app container:

```powershell
docker compose exec app python -m unittest discover -s tests -v
```

The included unit tests use synthetic IDs and fixture values. They do not require or include the clinical CSV. The suite does not validate live PostgreSQL retrieval, actual Presidio detection quality, semantic relevance, live model responses, or full UI behavior.

The optional `scripts/06_test_guardrails.py` sends test prompts to the configured model provider and may incur provider usage. It is not part of the unit-test command.

## Responsible use and limitations

- There is no authentication or authorization. A client-supplied patient ID is used as a retrieval filter; that does not establish that a caller may access the patient.
- Retrieval selects at most five nearest records and has no calibrated relevance threshold or independent semantic-relevance check.
- The question is embedded locally before redaction. Presidio recognizers can miss identifiers, and generated answers are not post-redacted.
- Guardrail instructions do not ensure factual accuracy or prevent unsupported content.
- Prompts are sent to an external model provider. Provider data handling and retention are not verified here.
- The project has not been clinically validated, security-certified, or established as compliant with healthcare regulations. It is not production-ready.

Do not use this prototype to make clinical decisions or process real patient information.
