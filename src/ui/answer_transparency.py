from typing import Any


BEHIND_ANSWER_TITLE = "Behind the Answer: Privacy, Retrieval & AI Guardrails"
PRIVACY_LIMITATION = (
    "Privacy and guardrail tools provide safeguards, but they do not guarantee "
    "complete redaction, factual accuracy, or clinical safety."
)

TECHNOLOGY_DETAILS = (
    (
        "PostgreSQL + pgvector",
        "Stores encounter records and retrieves up to five candidate records by "
        "semantic similarity using the selected patient filter.",
    ),
    (
        "Sentence Transformers / BioClinical ModernBERT",
        "Creates local embeddings for semantic retrieval. The latest question is "
        "embedded before Presidio redaction.",
    ),
    (
        "Presidio",
        "Attempts to detect and redact sensitive details from retrieved record "
        "context and the latest question before model generation.",
    ),
    (
        "NeMo Guardrails",
        "Applies the configured interaction instructions to the prompt and model "
        "workflow. Retrieved-record relevance is not independently verified, "
        "and guardrails do not guarantee a safe or correct answer.",
    ),
    (
        "Groq",
        "The configured Groq-compatible endpoint generates answers from the "
        "redacted prompt. Prompts are sent to an external provider.",
    ),
)


def render_behind_answer(
    streamlit: Any,
    evidence: list[dict[str, str]],
) -> None:
    with streamlit.expander(BEHIND_ANSWER_TITLE):
        if evidence:
            streamlit.markdown(
                "**Retrieved context (redacted; relevance is not independently verified):**"
            )
            for record in evidence:
                streamlit.write(record["snippet"])
        else:
            streamlit.write("No patient records were retrieved for this answer.")

        streamlit.markdown("**Technologies in this workflow:**")
        for name, description in TECHNOLOGY_DETAILS:
            streamlit.markdown(f"- **{name}:** {description}")
        streamlit.caption(PRIVACY_LIMITATION)
