import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from nemoguardrails import LLMRails, RailsConfig
from pydantic import BaseModel, Field, field_validator, model_validator
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, text

from src.database.connection import build_database_url
from src.pii_redaction.presidio_service import ClinicalPIIRedactor

load_dotenv()

app = FastAPI(title="Clinical RAG Demo API")
logger = logging.getLogger(__name__)
middleware = {}


@app.on_event("startup")
async def startup_event():
    print("Initializing application components...")
    middleware["redactor"] = ClinicalPIIRedactor()
    config = RailsConfig.from_path("./src/guardrails")
    middleware["rails"] = LLMRails(config)
    print("Loading local BioClinical ModernBERT embedding model...")
    middleware["embedder"] = SentenceTransformer(
        "NeuML/bioclinical-modernbert-base-embeddings"
    )
    print("Application components are ready.")


@lru_cache(maxsize=1)
def get_db_engine():
    return create_engine(build_database_url())


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, content: str) -> str:
        if not content.strip():
            raise ValueError("Message content must not be blank.")
        return content


class ChatRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    messages: List[ChatMessage] = Field(min_length=1)

    @field_validator("patient_id")
    @classmethod
    def patient_id_must_be_positive_integer(cls, patient_id: str) -> str:
        if not patient_id.isdecimal() or not 0 < int(patient_id) <= 9223372036854775807:
            raise ValueError("patient_id must be a positive integer.")
        return patient_id

    @model_validator(mode="after")
    def latest_message_must_be_from_user(self):
        if self.messages[-1].role != "user":
            raise ValueError("The latest message must be from the user.")
        return self


class ClinicalQuery(BaseModel):
    patient_id: str
    prompt: str = Field(min_length=1)


@dataclass(frozen=True)
class RetrievedPatientContext:
    prompt_context: str
    evidence: list[dict[str, str]]


INSUFFICIENT_EVIDENCE_RESPONSE = (
    "The available records do not provide enough evidence to answer this question."
)


@app.post("/api/v1/clinical-query")
async def process_clinical_query(query: ClinicalQuery):
    try:
        raw_context = """
        Synthetic patient Alex Example was admitted on a fictional date.
        A synthetic medication entry records a sample dose and route.
        Attending clinician: Casey Example.
        """
        redactor = middleware["redactor"]
        safe_context = redactor.redact_clinical_context(raw_text=raw_context)
        safe_prompt = redactor.redact_clinical_context(raw_text=query.prompt)
        prompt = f"Clinical Context:\n{safe_context}\n\nUser Question: {safe_prompt}"
        response = await middleware["rails"].generate_async(
            messages=[{"role": "user", "content": prompt}]
        )
        if not isinstance(response.get("content"), str):
            raise ValueError("Guardrails returned an invalid response.")
    except Exception as exc:
        logger.error("Mock clinical query processing failed.")
        raise HTTPException(
            status_code=502,
            detail="The mock clinical query could not be completed.",
        ) from exc

    return {
        "status": "success",
        "redacted_context_used": safe_context.strip(),
        "llm_response": response["content"],
    }


def build_patient_context(
    patient_id: str,
    question: str,
) -> RetrievedPatientContext:
    query_vector = middleware["embedder"].encode(question).tolist()
    with get_db_engine().connect() as conn:
        rows = conn.execute(text("""
            SELECT drug, dose_val_rx, dose_unit_rx, route, eventtype, test_name,
                   comments, description
            FROM patient_encounters
            WHERE subject_id = :subject_id AND clinical_embedding IS NOT NULL
            ORDER BY clinical_embedding <=> CAST(:query_embedding AS vector)
            LIMIT 5;
        """), {
            "subject_id": int(patient_id),
            "query_embedding": str(query_vector),
        }).fetchall()

    evidence = []
    redactor = middleware["redactor"]
    for row in rows:
        fields = (
            ("Drug", row.drug),
            ("Dose", " ".join(
                value for value in (row.dose_val_rx, row.dose_unit_rx) if value
            )),
            ("Route", row.route),
            ("Event", row.eventtype),
            ("Test", row.test_name),
            ("Comments", row.comments),
            ("Description", row.description),
        )
        raw_snippet = "\n".join(
            f"{label}: {value.strip() if isinstance(value, str) else value}"
            for label, value in fields
            if value is not None and str(value).strip()
        )
        if not raw_snippet:
            continue

        safe_snippet = redactor.redact_clinical_context(raw_text=raw_snippet).strip()
        if safe_snippet:
            evidence.append({"snippet": safe_snippet})

    prompt_context = "\n\n".join(
        f"[Retrieved patient record]\n{record['snippet']}" for record in evidence
    )
    return RetrievedPatientContext(
        prompt_context=prompt_context,
        evidence=evidence,
    )


@app.post("/api/v1/chat")
async def process_chat(request: ChatRequest):
    latest_question = request.messages[-1].content
    try:
        retrieved = build_patient_context(request.patient_id, latest_question)
    except Exception as exc:
        logger.error("Patient context retrieval failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Patient context could not be retrieved.",
        ) from exc

    if not retrieved.evidence:
        return {
            "status": "success",
            "llm_response": INSUFFICIENT_EVIDENCE_RESPONSE,
            "evidence": [],
        }

    try:
        redactor = middleware["redactor"]
        safe_question = redactor.redact_clinical_context(
            raw_text=latest_question
        )
        messages = [{
            "role": "user",
            "content": (
                "Answer only with facts directly supported by the supplied "
                "retrieved records. If the records do not contain the specific "
                "requested information, say it was not found in the available "
                "evidence. Do not infer or fill in missing clinical details.\n\n"
                f"Clinical Context:\n{retrieved.prompt_context}\n\n"
                f"User Question: {safe_question}"
            ),
        }]
        response = await middleware["rails"].generate_async(messages=messages)
        if not isinstance(response.get("content"), str):
            raise ValueError("Guardrails returned an invalid response.")
    except Exception as exc:
        logger.error("Guardrails response generation failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=502,
            detail="The language-model response could not be generated.",
        ) from exc

    return {
        "status": "success",
        "llm_response": response["content"],
        "evidence": retrieved.evidence,
    }


@app.get("/api/v1/patients")
async def get_unique_patients():
    try:
        with get_db_engine().connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT subject_id
                FROM patient_encounters
                WHERE subject_id IS NOT NULL AND clinical_embedding IS NOT NULL
                ORDER BY subject_id;
            """))
            patients = [str(row[0]) for row in result]
    except Exception as exc:
        logger.error("Available-patient lookup failed (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="Available patients could not be retrieved.",
        ) from exc

    return {"patients": patients if patients else ["No embedded patients found"]}
