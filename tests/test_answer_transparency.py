import unittest
from contextlib import contextmanager

from src.ui.answer_transparency import (
    BEHIND_ANSWER_TITLE,
    PRIVACY_LIMITATION,
    render_behind_answer,
)


class FakeStreamlit:
    def __init__(self):
        self.expander_titles = []
        self.markdown_content = []
        self.captions = []
        self.written_content = []

    @contextmanager
    def expander(self, title):
        self.expander_titles.append(title)
        yield

    def markdown(self, content):
        self.markdown_content.append(content)

    def caption(self, content):
        self.captions.append(content)

    def write(self, content):
        self.written_content.append(content)


class AnswerTransparencyTests(unittest.TestCase):
    def test_section_shows_retrieved_evidence_and_accurate_technology_details(self):
        streamlit = FakeStreamlit()

        render_behind_answer(
            streamlit,
            [{"snippet": "Synthetic field: [REDACTED]\nSynthetic value: [REDACTED]"}],
        )

        self.assertEqual(streamlit.expander_titles, [BEHIND_ANSWER_TITLE])
        self.assertIn(
            "Synthetic field: [REDACTED]\nSynthetic value: [REDACTED]",
            streamlit.written_content,
        )
        displayed_details = "\n".join(streamlit.markdown_content)
        self.assertIn("relevance is not independently verified", displayed_details)
        self.assertNotIn("row ID", displayed_details)
        for technology in (
            "PostgreSQL + pgvector",
            "Sentence Transformers / BioClinical ModernBERT",
            "Presidio",
            "NeMo Guardrails",
            "Groq",
        ):
            with self.subTest(technology=technology):
                self.assertIn(technology, displayed_details)
        self.assertIn(PRIVACY_LIMITATION, streamlit.captions)

    def test_section_explains_when_no_records_were_retrieved(self):
        streamlit = FakeStreamlit()

        render_behind_answer(streamlit, [])

        self.assertIn(
            "No patient records were retrieved for this answer.",
            streamlit.written_content,
        )


if __name__ == "__main__":
    unittest.main()
