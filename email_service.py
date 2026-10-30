import smtplib
from email.message import EmailMessage

from config import EMAIL_HOST, EMAIL_PASSWORD, EMAIL_PORT, FROM_EMAIL


# Oddiy def: smtplib bloklovchi, FastAPI uni alohida thread'da ishga tushiradi.
def send_welcome_email(email: str):
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
