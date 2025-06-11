# shop/utils.py
import requests
from django.conf import settings


def send_telegram_message(message):
    """
    Send a message to a Telegram chat using the bot.
    """
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'  # Optional: Use HTML for formatting
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Failed to send Telegram message: {e}")
        return None