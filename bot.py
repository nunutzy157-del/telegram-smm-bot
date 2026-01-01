import os
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://xtrasmm.in/api/v2"  # change if needed
USERS_FILE = "users.json"

# ---------- helpers ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def api_request(api_key, data):
    payload = {"key": api_key, **data}
    r = requests.post(API_URL, data=payload, timeout=30)
    return r.json()

# ---------- bot handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    uid = str(update.effective_user.id)

    if uid in users:
        await update.message.reply_text("✅ API key already saved.\nSend order ID or command.")
    else:
        await update.message.reply_text("🔐 Please send your SMM API key.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    uid = str(update.effective_user.id)
    text = update.message.text.strip()

    # Save API key
    if uid not in users:
        users[uid] = text
        save_users(users)
        await update.message.reply_text("✅ API key saved successfully!")
        return

    api_key = users[uid]
    parts = text.lower().split()

    # Order status check
    if len(parts) == 1 and parts[0].isdigit():
        order_id = parts[0]
        res = api_request(api_key, {
            "action": "status",
            "order": order_id
        })

        if "error" in res:
            await update.message.reply_text("❌ This is not your order ID.")
        else:
            msg = (
                f"📦 Order ID: {order_id}\n"
                f"📌 Status: {res.get('status')}\n"
                f"⚙️ Service: {res.get('service')}\n"
                f"💰 Charge: {res.get('charge')}\n"
                f"🔢 Start: {res.get('start_count')}\n"
                f"📉 Remains: {res.get('remains')}"
            )
            await update.message.reply_text(msg)
        return

    # Order actions
    if len(parts) >= 2 and parts[0].isdigit():
        order_id = parts[0]
        action_map = {
            "speed": "speed",
            "cancel": "cancel",
            "partial": "partial",
            "refill": "refill",
            "fake": "fake_complete"
        }

        cmd = parts[1]
        if cmd not in action_map:
            await update.message.reply_text("❌ Invalid command.")
            return

        res = api_request(api_key, {
            "action": action_map[cmd],
            "order": order_id
        })

        if "error" in res:
            await update.message.reply_text("❌ This is not your order ID.")
        else:
            await update.message.reply_text(f"✅ Action `{cmd}` processed for Order {order_id}")
        return

    await update.message.reply_text("❌ Invalid format.\nExample:\n123456 cancel")

# ---------- main ----------
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
