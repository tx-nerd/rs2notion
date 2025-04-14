import requests
import os
from datetime import datetime

# Load secrets from GitHub Actions or .env
RS_API_KEY = os.getenv("RS_API_KEY")
RS_BASE_URL = "https://txnerd.repairshopr.com/api/v1"
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")

def fetch_tickets():
    headers = {"Authorization": f"Bearer {RS_API_KEY}"}
    response = requests.get(f"{RS_BASE_URL}/tickets", headers=headers)
    response.raise_for_status()
    return response.json().get("tickets", [])

def send_to_make(ticket):
    due_date = ticket.get("due_date") or ticket.get("created_at")
    payload = {
