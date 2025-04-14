import requests
import os
from datetime import datetime

RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

def fetch_tickets():
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers)
    response.raise_for_status()
    return response.json().get("tickets", [])

def send_to_make(ticket):
    payload = {
        "id": ticket["id"],
        "subject": ticket["subject"],
        "status": ticket["status"],
        "due_date": ticket.get("due_date") or ticket.get("created_at")
    }
    response = requests.post(MAKE_WEBHOOK_URL, json=payload)
    response.raise_for_status()
    print(f"📤 Sent ticket #{ticket['id']} to Make")

def main():
    tickets = fetch_tickets()
    for ticket in tickets:
        if ticket.get("status") != "Resolved":
            send_to_make(ticket)

if __name__ == "__main__":
    main()
