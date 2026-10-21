from collections.abc import MutableMapping
from typing import Any


def initialize_patient_chat_state(
    session_state: MutableMapping[str, Any],
    patient_id: str,
) -> None:
    if session_state.get("active_patient_id") != patient_id:
        session_state["active_patient_id"] = patient_id
        session_state["messages"] = []
    else:
        session_state.setdefault("messages", [])
