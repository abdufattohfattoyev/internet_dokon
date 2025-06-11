# shop/tasks.py
from celery import shared_task
import requests
from django.conf import settings

@shared_task
def send_telegram_message_async(message):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Telegram xabarni yuborishda xato: {e}")
        return None