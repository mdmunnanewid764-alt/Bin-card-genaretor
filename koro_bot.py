import os
import sys
import time
import random
import json
import threading
import requests
from flask import Flask

# ── Configuration ───────────────────────────────────────────────────

BOT_TOKEN = "9119429503:AAFe8RC5AU-qWD3MqyQFB4UNZPbWe-xsrM0"
ADMIN_ID = 6575066703
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ── Flask health-check server (keeps Render happy) ──────────────────

app = Flask(__name__)

@app.route("/")
def index():
    return "BIN Card Generator Bot is running!", 200

@app.route("/health")
def health():
    return "OK", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    # Use gunicorn in production (Linux/Render), Flask dev server locally
    try:
        from gunicorn.app.base import BaseApplication

        class GunicornApp(BaseApplication):
            def __init__(self, application, options=None):
                self.application = application
                self.options = options or {}
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)

            def load(self):
                return self.application

        options = {"bind": f"0.0.0.0:{port}", "workers": 1, "loglevel": "info"}
        GunicornApp(app, options).run()
    except ImportError:
        # Fallback for Windows / local dev
        app.run(host="0.0.0.0", port=port)


# ── Card generation helpers ─────────────────────────────────────────

def luhn_checksum(card_number: str) -> int:
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    total = sum(odd_digits)
    for d in even_digits:
        total += sum(divmod(d * 2, 10))
    return total % 10


def generate_card(pattern: str) -> str:
    card = ""
    for ch in pattern:
        if ch.lower() == "x":
            card += str(random.randint(0, 9))
        else:
            card += ch
    card = card[:-1] + "0"
    check = luhn_checksum(card)
    last_digit = (10 - check) % 10
    card = card[:-1] + str(last_digit)
    return card


def normalize_pattern(raw: str) -> str:
    pattern = "".join(c for c in raw if c.isdigit() or c.lower() == "x")
    if len(pattern) < 16:
        pattern += "x" * (16 - len(pattern))
    return pattern[:16]


def generate_cards(pattern: str, count: int = 10) -> list[str]:
    pattern = normalize_pattern(pattern)
    cards: set[str] = set()
    attempts = 0
    while len(cards) < count and attempts < count * 20:
        cards.add(generate_card(pattern))
        attempts += 1
    return sorted(cards)


def generate_expiry() -> str:
    month = random.randint(1, 12)
    year = random.randint(25, 30)
    return f"{month:02d}/{year}"


def generate_cvv() -> str:
    return f"{random.randint(0, 999):03d}"


def build_card_message(pattern: str) -> str:
    clean = normalize_pattern(pattern)
    cards = generate_cards(clean, count=10)
    lines = []
    for card in cards:
        exp = generate_expiry()
        cvv = generate_cvv()
        lines.append(f"`{card}|{exp}|{cvv}`")
    header = f"\U0001f4b3 *Generated Cards for BIN* `{clean[:6]}`\n\n"
    return header + "\n".join(lines)


# ── Telegram API helpers ────────────────────────────────────────────

def send_message(chat_id: int, text: str, reply_markup: dict = None) -> None:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[send_message] error: {e}", file=sys.stderr)


def edit_message(chat_id: int, message_id: int, text: str, reply_markup: dict = None) -> None:
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{API_URL}/editMessageText", json=payload, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[edit_message] error: {e}", file=sys.stderr)


def answer_callback(callback_query_id: str, text: str = "") -> None:
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(f"{API_URL}/answerCallbackQuery", json=payload, timeout=10)
    except Exception as e:
        print(f"[answer_callback] error: {e}", file=sys.stderr)


def regen_keyboard(pattern: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "\U0001f504 Regenerate", "callback_data": f"regen:{pattern}"}]
        ]
    }


def get_updates(offset: int = None, timeout: int = 30):
    params = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=timeout + 5)
        r.raise_for_status()
        data = r.json()
        return data.get("result", [])
    except Exception as e:
        print(f"[get_updates] error: {e}", file=sys.stderr)
        return []


# ── Update handlers ─────────────────────────────────────────────────

def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text.startswith("/start"):
        send_message(
            chat_id,
            "\U0001f916 *BIN Card Generator Bot*\n\n"
            "Use `/gen <BIN>` to generate cards.\n\n"
            "*Example:*\n"
            "`/gen 527912xxxxxxxxxx`\n"
            "`/gen 527912`\n\n"
            "Replace digits you want randomised with `x`.",
        )

    elif text.startswith("/gen"):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            send_message(chat_id, "Please provide a BIN.\n\n*Usage:* `/gen 527912xxxxxxxxxx`")
            return

        raw = parts[1].strip()
        pattern = normalize_pattern(raw)

        if len(pattern) < 6:
            send_message(chat_id, "BIN must be at least 6 digits.")
            return

        body = build_card_message(pattern)
        send_message(chat_id, body, reply_markup=regen_keyboard(pattern))

    elif text.startswith("/restart"):
        if chat_id == ADMIN_ID:
            send_message(chat_id, "Restarting...")
            os._exit(0)
        else:
            send_message(chat_id, "You are not authorized.")


def handle_callback(callback_query: dict) -> None:
    cb_id = callback_query["id"]
    data = callback_query.get("data", "")
    message = callback_query.get("message")

    if not message or not data.startswith("regen:"):
        answer_callback(cb_id)
        return

    pattern = data[len("regen:"):]
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    body = build_card_message(pattern)
    edit_message(chat_id, message_id, body, reply_markup=regen_keyboard(pattern))
    answer_callback(cb_id, "Regenerated!")


def handle_update(update: dict) -> None:
    if "callback_query" in update:
        handle_callback(update["callback_query"])
    elif "message" in update or "edited_message" in update:
        msg = update.get("message") or update.get("edited_message")
        if msg:
            handle_message(msg)


# ── Bot polling loop ────────────────────────────────────────────────

def run_bot():
    print("Koro Telegram bot started. Polling for updates...")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            handle_update(update)
        time.sleep(0.5)


# ── Main ────────────────────────────────────────────────────────────

def main() -> None:
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run the bot polling in the main thread
    run_bot()


if __name__ == "__main__":
    main()
