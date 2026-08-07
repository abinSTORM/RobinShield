from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from core.scanner import get_token_info

import os

# Load .env file
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Runs when user types /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Robinhood Rug Checker!\n\n"
        "Paste a Robinhood Chain token contract address."
    )


async def check_contract(update: Update, context: ContextTypes.DEFAULT_TYPE):

    address = update.message.text.strip()

    info = get_token_info(address)

    if info is None:
        await update.message.reply_text(
            "❌ Invalid contract or token not found."
        )
        return

    await update.message.reply_text(
        f"""📄 Token Information

🪙 Name: {info['name']}

🏷 Symbol: {info['symbol']}

🔢 Decimals: {info['decimals']}

💰 Supply: {info['supply']:,}
"""
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, check_contract)
)

print("🤖 Bot Running...")

app.run_polling()