import requests
import os
from datetime import datetime, timedelta, timezone
from dateutil import parser

RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
SYNC_FILE = "last_sync.txt"
SEEN_IDS_FILE = "seen_ticket_ids.txt"

# ✅ Manual toggle flags
FORCE_SYNC = False  # ⬅️ Flip this to True to ignore last sync timestamp and refresh everything
FORCE_LAST_50 = True  # ⬅️ Flip this to False to return to pulling tickets from last 100 hours

RS_TICKET_URL_BASE = "https://txnerd.repairshopr.com/tickets/"
DEFAULT_SYNC_HOURS = 100


def read_last_sync():
    if FORCE_SYNC or not os.path.exists(SYNC_FILE):
        return datetime.now(timezone.utc) - timedelta(hours=DEFAULT_SYNC_HOURS)
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

    if FORCE_LAST_50:
        print("🚨 FORCE_LAST_50 is enabled -- fetching until 50 recent tickets are collected")
        while True:
            params = {
                "page": page,
                "per_page": 50,
                "sort[column]": "created_at",
                "sort[direction]": "desc"
            }
            response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            page_tickets = result.get("tickets") or result
            if not page_tickets:
                break

            all_tickets.extend(page_tickets)

            if len(all_tickets) >= 50:
                break

            page += 1

        all_tickets.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        return all_tickets[:50]

    created_after = since_time.isoformat()
    while True:
        params = {
            "created_after": created_after,
            "page": page,
            "per_page": 50,
            "sort[column]": "created_at",
            "sort[direction]": "desc"
        }
        response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers, params=params)
        response.raise_for_status()
        tickets = response.json().get("tickets", [])
        if not tickets:
            break
        all_tickets.extend(tickets)
        page += 1

    return all_tickets


def hydrate_ticket(ticket_id):
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets/{ticket_id}", headers=headers)
    response.raise_for_status()
    ticket_data = response.json().get("ticket", {})
    print(f"🧪 Hydrated Ticket #{ticket_id} Data:", ticket_data)
    return ticket_data


def send_to_make(ticket):
    raw_date = ticket.get("due_date") or ticket.get("created_at")
    due_date_clean = None
    if raw_date:
        try:
            parsed = parser.isoparse(raw_date).date()
            due_date_clean = parsed.isoformat()
        except Exception as e:
            print(f"⚠️ Could not parse date for ticket #{ticket['number']}: {e}")

    assigned = ticket.get("assigned_user_name")
    location = ticket.get("location", {}).get("name")

    if not assigned:
        print(f"⚠️ Missing assigned_to for ticket #{ticket.get('number')}")
    if not location:
        print(f"⚠️ Missing location for ticket #{ticket.get('number')}")

    customer = ticket.get("customer", {})
    customer_firstname = customer.get("firstname")
    customer_lastname = customer.get("lastname")
    customer_phone = customer.get("phone") or customer.get("mobile")

    if not customer_firstname:
        print(f"⚠️ Missing customer firstname for ticket #{ticket.get('number')}")
    if not customer_phone:
        print(f"⚠️ Missing customer phone for ticket #{ticket.get('number')}")

    payload = {
        "number": ticket.get("number"),
        "subject": ticket.get("subject"),
        "due_date": due_date_clean,
        "ticket_url": f"{RS_TICKET_URL_BASE}{ticket.get('number')}",
        "customer_firstname": customer_firstname,
        "customer_lastname": customer_lastname,
        "customer_phone": customer_phone,
        "assigned_to": assigned,
        "location": location,
        "created_at": ticket.get("created_at"),
        "problem_type": ticket.get("problem_type")
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
