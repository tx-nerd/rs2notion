import requests
import os
from datetime import datetime

# ENV variables (store these securely in Render or local .env)
RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_TM_DB_ID")

def fetch_tickets():
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers)
    response.raise_for_status()
    return response.json().get("tickets", [])

def send_to_notion(ticket):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    due_date = ticket.get("due_date") or ticket.get("created_at")
    due_date = due_date.split("T")[0] if due_date else datetime.today().strftime("%Y-%m-%d")

    payload = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Name": {
                "title": [{"text": {"content": f"RS Ticket #{ticket['id']}: {ticket['subject']}"}}]
            },
            "Status": {
                "select": {"name": "Open" if ticket["status"] != "Resolved" else "Closed"}
            },
            "Due Date": {
                "date": {"start": due_date}
            }
        }
    }

    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    print(f"✅ Sent ticket #{ticket['id']} to Notion")

def main():
    tickets = fetch_tickets()
    for ticket in tickets:
        if ticket.get("status") != "Resolved":
            send_to_notion(ticket)

if __name__ == "__main__":
    main()
