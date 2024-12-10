import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from config.settings import SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD, KINDLE_EMAIL

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.sender_email = SENDER_EMAIL
        self.sender_password = SENDER_PASSWORD
        self.kindle_email = KINDLE_EMAIL

    def send_to_kindle(self, epub_path: str, subject: Optional[str] = None):
        """Send EPUB file to Kindle email address."""
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.kindle_email
        msg['Subject'] = subject or 'Translated Book for Kindle'

        # Attach EPUB file
        with open(epub_path, 'rb') as f:
            epub_attachment = MIMEApplication(f.read(), _subtype='epub')
            epub_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=epub_path.split('/')[-1]
            )
            msg.attach(epub_attachment)

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                return True
        except Exception as e:
            raise Exception(f"Email sending error: {str(e)}")

    def test_connection(self) -> bool:
        """Test SMTP connection and credentials."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                return True
        except Exception:
            return False
