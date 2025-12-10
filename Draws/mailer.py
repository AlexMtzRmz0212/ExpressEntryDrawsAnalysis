"""Module for sending email notifications."""
import smtplib
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

from config import Config

logger = logging.getLogger(__name__)

class EmailService:
    """Handles email notifications."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def send_email(self, subject: str, body: str, email_config: Dict[str, str]):
        """Send an email with the given subject and body."""
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(
                self.config.EMAIL_SETTINGS['smtp_server'],
                self.config.EMAIL_SETTINGS['smtp_port']
            )
            server.starttls()
            server.login(email_config['smtp_user'], email_config['smtp_password'])
            server.send_message(msg)
            server.quit()

            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")