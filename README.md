# 🛠️ RepairShopr → Notion Integration

This script automates syncing tickets from **RepairShopr** into your **Notion Task Manager theme** using a Make.com webhook.

---

## ✅ What It Does

- Pulls tickets from your RepairShopr instance
- Converts them into Notion tasks via webhook
- Uses the ticket's `subject` and `due_date` (or fallback `created_at`)
- Enriches each task with:
  - Customer name, email, phone
  - Location, ticket type, assigned tech
  - Problem type, status, custom fields

---

## ⚙️ Setup Instructions

### 1. **Environment Variables**
Set these in your GitHub Actions secrets or `.env`:
- `RS_API_KEY` – Your RepairShopr API key
- `MAKE_WEBHOOK_URL` – Your custom webhook from Make

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Run via GitHub Actions**
This runs every 15 minutes, and can be manually triggered.

```yaml
# .github/workflows/schedule.yml
on:
  workflow_dispatch:
  schedule:
    - cron: '*/15 * * * *'
```

---

## 🧠 Sync Behavior

- Avoids duplicates using a Make search filter before insert
- Pulls **last 100 hours** if `last_sync.txt` doesn’t exist
- Respects `due_date` if present; falls back to `created_at`
- Stores last sync time in `last_sync.txt` (auto-created on first run)

---

## 📌 Coming Soon
- Two-way sync back to RepairShopr
- Customer & invoice creation
- Persistent job queue for failed sends
