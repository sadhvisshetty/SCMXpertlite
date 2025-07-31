import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

print(f"Testing with: {EMAIL_ADDRESS}, pwd length: {len(EMAIL_PASSWORD) if EMAIL_PASSWORD else 'None'}")

msg = MIMEText("This is a test email to verify SMTP credentials.")
msg["Subject"] = "SMTP Test"
msg["From"] = "ssadhvishetty1703@gmail.com"
msg["To"] = "ssadhvishetty1703@gmail.com"

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        print("1. Connecting to smtp.gmail.com:587")
        server.starttls()
        print("2. Starting TLS")
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        print("3. Logged in")
        server.send_message(msg)
    print("Test email sent successfully!")
except Exception as e:
    print(f" Test failed: {e}")
