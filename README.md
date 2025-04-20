🛠 RepairShopr to Notion Sync Script

This Python script pulls ticket data from RepairShopr and sends it to a Make.com webhook. It supports selective syncing, avoids duplicates, and is easy to toggle based on your workflow.

✅ Features

Pulls new tickets since the last sync or optionally fetches the latest 50 tickets.

Sends enriched ticket data to Make.com.

Logs ticket IDs to avoid duplicates.

📦 Installation

Clone your repository and install the required Python packages:

pip install -r requirements.txt

Create a .env file at the root of your project with these variables:

RS_API_KEY=your_repairshopr_api_key
MAKE_WEBHOOK_URL=https://hook.make.com/your-make-webhook-url

⚙️ Configuration Flags (In Code)

In repairshopr_pull.py, you can toggle these flags manually:

FORCE_SYNC = False      # ⬅️ Set to True to ignore last sync timestamp and re-pull everything
FORCE_LAST_50 = True    # ⬅️ Set to True to pull the latest 50 tickets regardless of time

You can use them together to re-pull the latest 50 tickets from scratch.

🧪 Usage

Run the script directly:

python repairshopr_pull.py

This will:

Use the last timestamp (unless FORCE_SYNC is enabled).

Optionally fetch only the latest 50 tickets (FORCE_LAST_50).

Hydrate full ticket data.

Send payload to Make.com.

Log sent IDs and update the sync timestamp.

🔍 Make.com Webhook Setup

Create a Make scenario with a custom webhook.

Copy the URL and paste it into your .env under MAKE_WEBHOOK_URL.

Map the payload fields inside Make to your Notion or desired action.

🚀 Git Push Workflow

This repo is designed for live use. Update repairshopr_pull.py locally, commit, then push live:

git add repairshopr_pull.py
git commit -m "Update flags or logic"
git push origin main

🔧 Example Output

⏱️ Last sync: 2025-04-20T15:44:00Z (FORCE_SYNC=False)
🚨 FORCE_LAST_50 is enabled -- pulling latest 50 tickets instead of using sync window
🧪 Hydrated Ticket #94032833 Data: {...}
📤 Sent ticket #23527 to Make