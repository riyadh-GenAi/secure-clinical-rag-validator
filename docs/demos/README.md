# Demo and media guide

## Available demo media

The following media files are available in the repository documentation area:

- [Main chat screenshot](../images/clinical-chat.png)
- [Transparency panel screenshot](../images/answer-transparency.png)
- [Safety / missing-information screenshot](../images/safety-behavior.png)
- [Demo video](clinical-rag-demo.mp4)

## What the demo illustrates

The demo shows a patient-selected context window, a question-and-answer interaction, the “Behind the Answer” panel, and a safe-answer guardrail pattern. It is intended to demonstrate how the prototype combines retrieval, redaction, and generation while making the retrieval context more inspectable.

## What each screenshot demonstrates

### Main chat view

This screenshot shows the patient selector and the interactive conversation pattern. It demonstrates the UI state, example user question, and the plain-language AI disclaimer that the prototype is not for diagnostic use.

### Transparency view

This screenshot opens the answer-transparency panel and exposes the retrieved evidence plus the technology notes used in the system. It is a demonstration of workflow transparency, not proof that the retrieved content is clinically complete or independently validated.

### Safety / missing-information example

This screenshot illustrates the guardrail behavior when the request cannot be answered using the available evidence. It shows the prototype’s safe fallback pattern rather than a guarantee of correct clinical guidance.

## Viewing sequence

1. Open the main chat screenshot to understand the patient-filtered workflow.
2. Review the transparency screenshot to inspect the retrieved snippets and technology notes.
3. Review the safety screenshot to understand the missing-information fallback behavior.
4. Watch the video last to see the interaction in motion.

## Privacy and publication notes

The patient IDs shown in the examples are synthetic. Other clinical-looking content has not been independently confirmed as synthetic. Before public distribution, a reviewer with knowledge of the source should confirm that the screenshots and every video frame/audio/caption are free of real patient information and that all publication rights are clear. Do not treat redaction or a synthetic patient ID as proof that every clinical detail is safe to publish.

The temporary source-media folder is not part of the intended final repository. The documentation copies are retained under `docs/`.

## Demonstration limitations

This prototype is not a medical advice system and is not a clinical decision support system. It does not validate retrieval quality or answer correctness independently, and it should not be used for diagnosis or treatment decisions.
