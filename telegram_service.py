import aiohttp

from config import TELEGRAM_BOT_TOKEN


async def send_telegram_message(chat_id: str, message: str):
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram bot token sozlanmagan, xabar yuborilmadi.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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
