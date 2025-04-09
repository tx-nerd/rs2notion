# RepairShopr → Notion Integration (Step 1)

## What it does:
- Pulls tickets from RepairShopr
- Converts them into tasks in your Notion "Task Manager" theme
- Uses ticket subject as the title and due_date (or created date) as the task's due date

## Setup Instructions:
1. Set environment variables in Render or .env:
   - `RS_API_KEY`
   - `NOTION_API_KEY`
   - `NOTION_DATABASE_ID`

2. Adjust the RepairShopr subdomain and Notion DB fields if necessary.

3. Deploy on Render as a Background Worker using `cron.yaml`.

## Notes:
- This script avoids creating duplicate tasks. Future versions should check Notion for existing tickets first.
- Runs every 30 minutes.

More steps coming soon: syncing customers, invoices, and webhook handling.
