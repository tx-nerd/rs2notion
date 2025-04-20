import requests
import os
from datetime import datetime, timedelta, timezone
from dateutil import parser

RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
SYNC_FILE = "last_sync.txt"
SEEN_IDS_FILE = "seen_ticket_ids.txt"
FORCE_SYNC = os.getenv("FORCE_SYNC", "false").lower() == "true"

RS_TICKET_URL_BASE = "https://txnerd.repairshopr.com/tickets/"

def read_last_sync():
    if FORCE_SYNC or not os.path.exists(SYNC_FILE):
        return datetime.now(timezone.utc) - timedelta(hours=100)
    with open(SYNC_FILE, "r") as f:
        return datetime.fromisoformat(f.read().strip()).astimezone(timezone.utc)

def write_last_sync(ts: datetime):
    with open(SYNC_FILE, "w") as f:
        f.write(ts.isoformat())

def load_seen_ids():
    if FORCE_SYNC or not os.path.exists(SEEN_IDS_FILE):
        return set()
    with open(SEEN_IDS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip().isdigit())

def save_seen_ids(ids):
    with open(SEEN_IDS_FILE, "w") as f:
        for tid in sorted(ids):
            f.write(f"{tid}\n")

def fetch_tickets(since_time: datetime):
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    page = 1
    all_tickets = []
    created_after = since_time.date().isoformat()

    while True:
        params = {
            "created_after": created_after,
            "page": page
        }
        response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers, params=params)
        response.raise_for_status()
        tickets = response.json().get("tickets", [])

        if not tickets:
            break

        all_tickets.extend(tickets)
        page += 1

    return [t for t in all_tickets if t.get("status") != "Resolved"]

def hydrate_ticket(ticket_id):
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets/{ticket_id}", headers=headers)
    response.raise_for_status()
    return response.json().get("ticket", {})

def send_to_make(ticket):
    raw_date = ticket.get("due_date") or ticket.get("created_at")
    due_date_clean = None
    if raw_date:
        try:
            parsed = parser.isoparse(raw_date).date()
            due_date_clean = parsed.isoformat()
        except Exception as e:
            print(f"⚠️ Could not parse date for ticket #{ticket['number']}: {e}")

    customer = ticket.get("customer", {})
    customer_first = customer.get("firstname", "")
    customer_last = customer.get("lastname", "")

    payload = {
        "number": ticket.get("number"),
        "subject": ticket.get("subject"),
        "due_date": due_date_clean,
        "ticket_url": f"{RS_TICKET_URL_BASE}{ticket.get('number')}",
        "customer_firstname": customer_first,
        "customer_lastname": customer_last,
        "customer_phone": customer.get("phone"),
        "assigned_to": ticket.get("assigned_user_name"),
        "location": ticket.get("location", {}).get("name"),
        "created_at": ticket.get("created_at"),
        "problem_type": ticket.get("problem_type"),
        "custom_fields": ticket.get("custom_fields")
    }

    print("🔍 Payload:", payload)

    try:
        response = requests.post(MAKE_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"📤 Sent ticket #{ticket['number']} to Make")
        return True
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Failed to send ticket #{ticket['number']}: {e}")
        return False

def main():
    last_sync = read_last_sync()
    print(f"⏱️ Last sync: {last_sync.isoformat()} (FORCE_SYNC={FORCE_SYNC})")
    seen_ids = load_seen_ids()
    tickets = fetch_tickets(last_sync)
    new_ids = set(seen_ids)

    for ticket in tickets:
        ticket_id = str(ticket["id"])
        if ticket_id in seen_ids:
            continue

        hydrated = hydrate_ticket(ticket["id"])
        if send_to_make(hydrated):
            new_ids.add(ticket_id)

    save_seen_ids(new_ids)
    write_last_sync(datetime.now(timezone.utc))

if __name__ == "__main__":
    main()
