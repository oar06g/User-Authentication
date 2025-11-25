import secrets
import string
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from configparser import ConfigParser
import ssl
from typing import Optional

from src.settings import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD

class INIConfig:
    def __init__(self, file_path: str = "config.ini"):
        self.file_path = file_path
        self.config = ConfigParser()
        try:
            read_files = self.config.read(self.file_path)
            if not read_files:
                print(f"Warning: {file_path} does not exist or is empty.")
        except Exception as e:
            print(f"Failed to read {file_path}: {e}")
    def get(self, section: str, option: str, fallback: Optional[str] = None) -> Optional[str]: 
        """Get a value from the config file."""
        try: return self.config.get(section, option, fallback=fallback)
        except Exception as e: print(f"Error getting [{section}]->{option}: {e}"); return fallback
    
    def set(self, section: str, option: str, value: str):
        """Set a value in the config file. Creates the section if it does not exist."""
        if not self.config.has_section(section):self.config.add_section(section)
        self.config.set(section, option, value)
    
    def sae(self):
        """Save changes to the config file."""
        try:
            with open(self.file_path, "w", encoding="utf-8") as f: self.config.write(f)
            print(f"Config saved to {self.file_path}")
        except Exception as e:
            print(f"Failed to save config: {e}")

CONFIG = INIConfig("config.ini")


def generate_secure_token(length: int = 32) -> str:
    """
    Generates a secure, random token with a `UA_` prefix.

    The token uses the secrets module for cryptographic strength and includes
    and includes uppercase letters, lowercase letters, digits.
    The final token will have a length of length +3 (for 'UA_').

    NOTE: 
    This is a placeholder implementation. 
    In a production environment, it needs to be developed further.

    Args:
        length: The length of the random part of the token (default 32).
    
    Returns:
        A string representing the unique token.
    """

    prefix = "UA_"
    alphabet = string.ascii_letters + string.digits
    token_suffix = ''.join(secrets.choice(alphabet) for _ in range(length))
    secure_token = f"{prefix}{token_suffix}"
    return secure_token

def send_email(to_email: str, subject: str, body: str):
    """
    Send an email via SMTP

    Args:
    to_email (str): Recipient email address
    subject (str): Subject of the email
    body (str): Body content of the email
    """

    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    part1 = MIMEText(body, 'html', "utf-8")
    msg.attach(part1)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

class EmailTemplate:
    @classmethod
    def email_template(self, fullname: str, verify_link: str) -> str:
        email_title = "Email Verification"
        email_body = f"""<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>Welcome to {CONFIG.get("APP", "app_name")}</h2>
    <p>Hello {fullname},</p>
    <p>Thank you for signing up. Please verify your email address to activate your account:</p>
    <p style="text-align: center;">
      <a href="{verify_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
        Verify Email
      </a>
    </p>
    <p>This link will expire in 24 hours.</p>
    <p>If you did not create this account, you can ignore this email.</p>
    <br>
    <p>Best regards,<br>The {CONFIG.get("APP", "app_name")} Team</p>
  </body>
</html>
"""
        return email_title, email_body


# TO_EMAIL = "omar20729193@gmail.com"
# SUBJECT, BODY = EmailTemplate.email_template("Omar", verify_link="https://google.com")

# send_email(TO_EMAIL, SUBJECT, BODY)

