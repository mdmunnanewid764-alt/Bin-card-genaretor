import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Bot configuration (replace with your own token if needed)
BOT_TOKEN = "9119429503:AAFe8RC5AU-qWD3MqyQFB4UNZPbWe-xsrM0"
ADMIN_ID = 6575066703

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "🤖 Welcome! Use /gen to generate a random BIN number."
    )

async def gen_bin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a random 6‑digit BIN number and send it to the user.

    A BIN (Bank Identification Number) is the first 6 digits of a payment
    card number. The range 400000‑599999 covers most Visa‑type BINs, but the
    function simply returns any 6‑digit number to keep it generic.
    """
    # Only allow the admin (or any user) – here we allow everyone.
    bin_number = random.randint(400000, 599999)
    await update.message.reply_text(f"💳 Your random BIN is: `{bin_number}`", parse_mode="Markdown")

async def admin_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Allow the admin to restart the bot via /restart command."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to restart the bot.")
        return
    await update.message.reply_text("🔄 Restarting... (please wait a few seconds)")
    # Simple way: exit the process; a supervising service should restart it.
    os._exit(0)

import asyncio

def main() -> None:
    """Start the Telegram bot.

    Builds the Application, registers command handlers, and runs the async
    polling loop using ``asyncio.run`` for proper event‑loop handling.
    """
    async def _run() -> None:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("gen", gen_bin))
        app.add_handler(CommandHandler("restart", admin_restart))
        await app.run_polling()
    asyncio.run(_run())

if __name__ == "__main__":
    main()
