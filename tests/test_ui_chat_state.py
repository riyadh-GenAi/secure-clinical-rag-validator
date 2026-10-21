import unittest

from src.ui.chat_state import initialize_patient_chat_state


class PatientChatStateTests(unittest.TestCase):
    def test_switching_patients_clears_the_previous_conversation(self):
        state = {
            "active_patient_id": "900000001",
            "messages": [
                {"role": "user", "content": "Previous patient's question"},
                {"role": "assistant", "content": "Previous patient's answer"},
            ],
        }

        initialize_patient_chat_state(state, "900000002")

        self.assertEqual(state["active_patient_id"], "900000002")
        self.assertEqual(state["messages"], [])

    def test_same_patient_keeps_the_existing_conversation(self):
        messages = [{"role": "user", "content": "Follow-up question"}]
        state = {"active_patient_id": "900000001", "messages": messages}

        initialize_patient_chat_state(state, "900000001")

        self.assertIs(state["messages"], messages)

    def test_first_patient_selection_initializes_empty_state(self):
        state = {}

        initialize_patient_chat_state(state, "900000001")

        self.assertEqual(state, {"active_patient_id": "900000001", "messages": []})


if __name__ == "__main__":
    unittest.main()
