from locust import HttpUser, task, between
import random
import uuid
import datetime

class VetlogLoadTester(HttpUser):
    # Wait between 0.5 and 2 seconds between tasks
    wait_time = between(0.5, 2.0)

    @task(3)
    def simulate_whatsapp_ingestion(self):
        """Simulates the Chrome Extension sending WhatsApp messages to the backend"""
        payload = {
            "messages": [
                {
                    "id": str(uuid.uuid4()),
                    "chat_name": random.choice(["Donations Group", "General Chat", "Emergencies"]),
                    "sender": "Test User",
                    "text": random.choice([
                        "Patient Rocky treatment complete",
                        "Rs 5000 donation from JDC",
                        "Can you check on Daisy?",
                        "Schedule an appointment for tomorrow at 2PM"
                    ]),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ]
        }
        self.client.post("/webhook/extension/batch/", json=payload)

    @task(1)
    def simulate_ai_chat(self):
        """Simulates a doctor asking the AI a question"""
        payload = {
            "message": random.choice([
                "How many donations did we receive today?",
                "Give me a daily summary report",
                "What happened with Rocky?"
            ]),
            "thread_id": "load_test_thread",
            "user_id": 1
        }
        # Hit the streaming endpoint
        with self.client.post("/chat/stream/", json=payload, stream=True, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got {response.status_code}")
