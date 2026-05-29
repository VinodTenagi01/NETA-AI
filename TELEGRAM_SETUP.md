# NETA.AI — Telegram Integration Setup Guide

## What This Integration Does

Sends NETA.AI campaign alerts to a private Telegram group or channel:
- Campaign alerts (booth divergence, opposition activity, SLA breaches)
- Daily campaign summaries
- System notifications

No external library needed — uses the Telegram Bot HTTP API directly via httpx.

---

## Step 1 — Create a Telegram Bot

1. Open Telegram → search for **@BotFather**
2. Send `/newbot`
3. Choose a bot name: e.g. `NETA AI Alerts`
4. Choose a username: e.g. `neta_ai_alerts_bot` (must end in `bot`)
5. BotFather will give you a token: `1234567890:ABCDEFxxxxxxxxxxxxxxxxxxxxxxxx`
6. **Save this token** — this is your `TELEGRAM_BOT_TOKEN`

---

## Step 2 — Create a Private Group

1. Create a new Telegram group (e.g. "NETA.AI Campaign Command")
2. Add your bot to the group as a member
3. Make the bot an **admin** (needed to send messages)

---

## Step 3 — Get the Chat ID

**Option A — Using the bot's getUpdates API:**
1. Send any message to the group (e.g. "hello")
2. Open this URL in browser (replace `YOUR_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for `"chat": {"id": -1001234567890, ...}` in the response
4. The negative number is your `TELEGRAM_CHAT_ID` (groups/channels have negative IDs)

**Option B — Add @userinfobot to your group:**
1. Add `@userinfobot` to the group
2. It will reply with the chat ID
3. Remove it after getting the ID

---

## Step 4 — Configure .env

Add to your `.env` file:
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-1001234567890
TELEGRAM_ENABLED=true
```

---

## Step 5 — Restart API

```powershell
cd D:\NETA.AI
docker compose restart api celery-worker
```

---

## Step 6 — Test

```powershell
# Get auth token
$auth = Invoke-RestMethod "http://localhost:8000/api/auth/login" `
    -Method POST `
    -Body '{"email":"admin@netaai.in","password":"Admin123!Secure"}' `
    -ContentType "application/json"

$headers = @{ Authorization = "Bearer $($auth.access_token)" }

# Check health
Invoke-RestMethod "http://localhost:8000/api/telegram/health" | ConvertTo-Json

# Send test message
Invoke-RestMethod "http://localhost:8000/api/telegram/test-alert" `
    -Method POST `
    -Headers $headers `
    -Body '{"message":"NETA.AI is connected to Telegram!"}' `
    -ContentType "application/json"
```

You should receive a test message in your Telegram group within seconds.

---

## Available API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/telegram/health` | None | Configuration + bot status |
| `POST` | `/api/telegram/test-alert` | Admin | Send test message |
| `POST` | `/api/telegram/send-alert` | Admin | Send formatted campaign alert |
| `POST` | `/api/telegram/setup-webhook` | Super Admin | Register webhook for bot commands |
| `POST` | `/api/telegram/webhook` | None | Receive Telegram updates (bot commands) |

---

## Send a Campaign Alert via API

```bash
POST /api/telegram/send-alert
Authorization: Bearer <token>

{
  "title": "Booth 47 Divergence Alert",
  "description": "Opposition canvassing activity detected near GHMC school booth.",
  "severity": "HIGH",
  "alert_type": "DIVERGENCE",
  "booth_name": "GHMC PS Hafeezpet",
  "zone_name": "Zone A",
  "action_required": "Deploy field worker immediately"
}
```

This will send a formatted message to your Telegram group.

---

## Bot Commands (if webhook is configured)

After setting up the webhook endpoint, the bot responds to:

| Command | Response |
|---|---|
| `/status` | System health status |
| `/help` | List of available commands |

To enable webhooks (requires HTTPS URL):
```bash
POST /api/telegram/setup-webhook
{
  "webhook_url": "https://neta-api.onrender.com/api/telegram/webhook"
}
```

Webhooks only work on HTTPS. For local testing, use polling or ngrok.

---

## Render Configuration

Add to Render's environment variables for `neta-api` and `neta-celery-worker`:

```
TELEGRAM_BOT_TOKEN = <your token>
TELEGRAM_CHAT_ID   = <your chat ID>
TELEGRAM_ENABLED   = true
```

---

## Alert Format Example

```
🚨 NETA.AI ALERT — CRITICAL

📊 Booth 47 Divergence Alert

Opposition canvassing activity detected near GHMC school booth.

🏛 Booth: GHMC PS Hafeezpet
🗺 Zone: Zone A

❗ Action required: Deploy field worker immediately

🕒 29 May 2026 14:35 IST
```

---

## Security Notes

- The bot token is sensitive — never commit it to git
- Only the bot can read messages in the group (other members cannot issue commands to the bot unless you implement authorization)
- The `/api/telegram/webhook` endpoint is unauthenticated (Telegram calls it) but only processes Telegram-formatted payloads
- For production, consider restricting webhook access to Telegram's IP ranges: `149.154.160.0/20` and `91.108.4.0/22`
