import streamlit as st
import requests

from answer_transparency import render_behind_answer
from chat_state import initialize_patient_chat_state

API_CHAT_URL = "http://localhost:8000/api/v1/chat"
API_PATIENTS_URL = "http://localhost:8000/api/v1/patients"

st.set_page_config(page_title="Clinical Record Chat Demo", layout="centered")
st.title("Clinical Record Chat Demo")
st.caption("Prototype using Presidio redaction and NeMo Guardrails.")

# --- FETCH PATIENTS DYNAMICALLY ---
@st.cache_data(ttl=300) # Cache the list for 5 minutes to reduce database load
def fetch_patient_list():
    try:
        response = requests.get(API_PATIENTS_URL)
        if response.status_code == 200:
            return response.json().get("patients", ["No patients found"])
    except:
        return ["Database Connection Error"]
    return ["Unknown Error"]

patient_list = fetch_patient_list()

# Streamlit's selectbox is automatically searchable!
patient_id = st.sidebar.selectbox("Select Patient File (Type to search)", patient_list)
st.sidebar.info(f"Selected patient filter: {patient_id}")

initialize_patient_chat_state(st.session_state, patient_id)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and "evidence" in msg:
            render_behind_answer(st, msg["evidence"])

# --- CHAT INPUT & API CALL ---
if prompt := st.chat_input(f"Ask about patient {patient_id}'s history..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    payload = {
        "patient_id": patient_id,
        "messages": st.session_state.messages
    }

    answer_evidence = None
    with st.spinner("Analyzing securely..."):
        try:
            response = requests.post(API_CHAT_URL, json=payload)
            response.raise_for_status()
            response_payload = response.json()
            if not isinstance(response_payload, dict):
                raise ValueError("The API returned an invalid response.")

            bot_reply = response_payload.get("llm_response")
            response_evidence = response_payload.get("evidence")
            if not isinstance(bot_reply, str) or not isinstance(response_evidence, list):
                raise ValueError("The API returned an invalid response.")
            if not all(
                isinstance(record, dict)
                and isinstance(record.get("snippet"), str)
                for record in response_evidence
            ):
                raise ValueError("The API returned invalid evidence.")
            answer_evidence = response_evidence

            # Enforce Output Disclaimer
            bot_reply += "\n\n*⚠️ AI generated summary. Do not use for diagnostic purposes.*"

        except requests.exceptions.RequestException as e:
            bot_reply = f"❌ API Error: {e}"
        except ValueError:
            bot_reply = "❌ API Error: The server returned an invalid response."

    assistant_message = {"role": "assistant", "content": bot_reply}
    if answer_evidence is not None:
        assistant_message["evidence"] = answer_evidence
    st.session_state.messages.append(assistant_message)
    with st.chat_message("assistant"):
        st.write(bot_reply)
        if answer_evidence is not None:
            render_behind_answer(st, answer_evidence)