from flask_mail import Mail, Message
from flask import current_app
from werkzeug.exceptions import BadRequest

from app.utils.base_logger import BaseLogger

app_logger = BaseLogger(logger_name="BaseService").get_logger()


class BaseMailer:
    def __init__(self, app=None):
        self.mail = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the mail extension with the app.
        """
        self.mail = Mail(app)

    def send_email(self, subject, recipients, html, body=None, sender=None, attachments=None):
        """
        Send an email with optional attachments.
        """
        if not self.mail:
            raise RuntimeError("Mail not initialized. Call init_app with a valid app instance.")

        if sender is None:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')

        if not isinstance(recipients, (list, tuple)):
            recipients = [recipients]

        # Create the email message
        msg = Message(
            subject=subject,
            recipients=recipients,
            body=body,
            html=html,
            sender=sender
        )

        # Attach any provided files
        if attachments:
            for filename, file_content in attachments:
                msg.attach(filename, 'application/octet-stream', file_content)

        try:
            with current_app.app_context():
                self.mail.send(msg)
                app_logger.info(f"Email sent successfully to {', '.join(recipients)}")
        except Exception as e:
            app_logger.error(f"Failed to send email to {recipients}: {e}")
            raise BadRequest("Failed to send email.")
