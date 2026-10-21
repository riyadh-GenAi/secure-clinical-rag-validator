from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

class ClinicalPIIRedactor:
    def __init__(self):
        print("Initializing Presidio redaction service...")
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # --- FDE FIX 1: Custom SSN Pattern Recognizer ---
        # Overrides the strict checksum to catch ANY xxx-xx-xxxx format
        ssn_pattern = Pattern(name="catch_all_ssn", regex=r"\d{3}-\d{2}-\d{4}", score=0.9)
        ssn_recognizer = PatternRecognizer(supported_entity="US_SSN", patterns=[ssn_pattern])
        self.analyzer.registry.add_recognizer(ssn_recognizer)

        # --- FDE FIX 2: Custom Deny-List for Medical Facilities ---
        # Forces Presidio to recognize specific hospital names as organizations
        hospital_recognizer = PatternRecognizer(
            supported_entity="ORGANIZATION",
            deny_list=["Massachusetts General Hospital", "Mayo Clinic", "Cleveland Clinic"],
            deny_list_score=1.0  # <--- Changed this from 'score'
        )
        self.analyzer.registry.add_recognizer(hospital_recognizer)

        self.target_entities = [
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "US_SSN",
            "LOCATION",
            "ORGANIZATION",
            "DATE_TIME"
        ]

    def redact_clinical_context(self, raw_text: str) -> str:
        if not raw_text:
            return ""

        analyzer_results = self.analyzer.analyze(
            text=raw_text,
            entities=self.target_entities,
            language='en',
            score_threshold=0.4
        )

        anonymized_result = self.anonymizer.anonymize(
            text=raw_text,
            analyzer_results=analyzer_results
        )

        return anonymized_result.text

if __name__ == "__main__":
    redactor = ClinicalPIIRedactor()

    simulated_ehr_note = """
    Synthetic patient Alex Example (SSN: 000-00-0000) was admitted to
    Synthetic Medical Center on a fictional date. Contact Casey Example at
    000-000-0000 or casey@example.invalid.
    """

    print("\nSynthetic input (not real patient data):")
    print(simulated_ehr_note.strip())

    print("\nRedaction demonstration output:")
    safe_text = redactor.redact_clinical_context(simulated_ehr_note)
    print(safe_text.strip())