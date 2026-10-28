# BIN Card Generator Telegram Bot 💳

A Telegram bot that generates Luhn-valid card numbers from a given BIN (Bank Identification Number).

## Features

- `/start` — Welcome message with usage instructions
- `/gen <BIN>` — Generate 10 Luhn-valid card numbers with expiry & CVV
- 🔄 **Regenerate** inline button to quickly generate new cards
- `/restart` — Admin-only bot restart

## Usage

```
/gen 527912xxxxxxxxxx
/gen 527912
```

Replace digits you want randomized with `x`. The bot pads to 16 digits automatically.

## Setup

1. Install dependencies:
   ```bash
   pip install requests
   ```

2. Run the bot:
   ```bash
   python koro_bot.py
   ```
   Or double-click `run.bat` on Windows.

## Configuration

Edit `koro_bot.py` to set:
- `BOT_TOKEN` — Your Telegram bot token
- `ADMIN_ID` — Your Telegram user ID (for `/restart`)
