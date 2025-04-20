import requests
import os
from datetime import datetime, timedelta
from dateutil import parser

RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
SYNC_FILE = "last_sync.txt"

def read_last_sync():
    if not os.path.exists(SYNC_FILE):
        # Default to 3 hours ago if no sync file exists
        return datetime.utcnow() - timedelta(hours=3)
    with open(SYNC_FILE, "r") as f:
        return datetime.fromisoformat(f.read().strip())

def write_last_sync(ts: datetime):
    with open(SYNC_FILE, "w") as f:
        f.write(ts.isoformat())

def fetch_tickets(since_time: datetime):
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers)
    response.raise_for_status()
    all_tickets = response.json().get("tickets", [])
    return [
        t for t in all_tickets
        if t.get("created_at")
        and parser.isoparse(t["created_at"]) > since_time
        and t.get("status") != "Resolved"
    ]

def send_to_make(ticket):
    payload = {
        "id": ticket["id"],
        "subject": ticket["subject"],
        "status": ticket["status"],
        "due_date": ticket.get("due_date"),
        "customer_name": ticket.get("customer", {}).get("name"),
        "customer_email": ticket.get("customer", {}).get("email"),
        "customer_phone": ticket.get("customer", {}).get("phone"),
        "ticket_type": ticket.get("ticket_type"),
        "assigned_to": ticket.get("assigned_user_name"),
        "location": ticket.get("location", {}).get("name"),
        "created_at": ticket.get("created_at"),
        "updated_at": ticket.get("updated_at"),
        "problem_type": ticket.get("problem_type"),
        "custom_fields": ticket.get("custom_fields")
    }

    try:
        response = requests.post(MAKE_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"📤 Sent ticket #{ticket['id']} to Make")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Failed to send ticket #{ticket['id']}: {e}")

def main():
    last_sync = read_last_sync()
    print(f"⏱️ Last sync: {last_sync.isoformat()}")
    tickets = fetch_tickets(last_sync)

    for ticket in tickets:
        send_to_make(ticket)

    # Save sync timestamp after all tickets have been processed
    write_last_sync(datetime.utcnow())

if __name__ == "__main__":
    main()
