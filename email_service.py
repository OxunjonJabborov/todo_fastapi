import os
import smtplib
from email.message import EmailMessage

import aiohttp
from dotenv import load_dotenv

load_dotenv()

FROM_EMAIL = os.getenv('FROM_EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))


TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')


async def send_welcome_email(email: str):
    if not FROM_EMAIL or not EMAIL_PASSWORD or not EMAIL_HOST:
        print("Email sozlamalari to'liq emas, xabar yuborilmadi.")
        return

    message = EmailMessage()
    message['Subject'] = 'Welcome to our service!'
    message['From'] = FROM_EMAIL
    message['To'] = email
    message.set_content(
        'Thank you for registering with our service. '
        'We are glad to have you on board!'
    )
    try:
        with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.login(FROM_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(message)
    except Exception as e:
        print(f"Error sending email to {email}: {e}")


async def send_telegram_message(chat_id: str, message: str):
    if not TOKEN:
        print("Telegram bot token sozlanmagan, xabar yuborilmadi.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"Failed to send Telegram message: {response.status}")
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
