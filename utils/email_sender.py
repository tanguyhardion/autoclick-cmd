import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def send_email(subject, body):
    """
    Send an email using Gmail SMTP.
    Requires GMAIL_EMAIL, GMAIL_APP_PASSWORD, and RECIPIENT_EMAIL in .env
    """
    try:
        gmail_email = os.getenv("GMAIL_EMAIL")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        recipient_email = os.getenv("RECIPIENT_EMAIL")

        if not all([gmail_email, gmail_password, recipient_email]):
            print("Error: Missing email configuration in .env file")
            print(f"  GMAIL_EMAIL: {bool(gmail_email)}")
            print(f"  GMAIL_APP_PASSWORD: {bool(gmail_password)}")
            print(f"  RECIPIENT_EMAIL: {bool(recipient_email)}")
            return False

        # Create message
        msg = MIMEMultipart()
        msg["From"] = gmail_email
        msg["To"] = recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_email, gmail_password)
            server.send_message(msg)

        print(f"Email sent successfully: {subject}")
        return True

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
