from app.EmailConfig.EmailBase import BaseMailer
from app.EmailConfig.EmailBulder import EmailBuilder

class EmailService:
    def __init__(self, mailer: BaseMailer):
        if not isinstance(mailer, BaseMailer):
            raise ValueError("A valid BaseMailer instance is required.")
        self.mailer = mailer

    def send_email(self, email_builder: EmailBuilder):
        """
        Sends the email using the BaseMailer after constructing it with EmailBuilder.
        """
        email_content = email_builder.get_email_content()
        return self.mailer.send_email(
            subject=email_content['subject'],
            recipients=email_builder.recipient_email,
            html=email_content['html'],
            body=email_content['body'],
            attachments=email_content['attachments']
        )

    def send_otp_email(self, first_name, otp, recipient_email):
        """
        Sends an OTP email using EmailBuilder.
        """
        email_builder = EmailBuilder(first_name, recipient_email).build_otp_email(otp)
        return self.send_email(email_builder)

    def send_resend_otp_email(self, first_name, otp, recipient_email):
        """
        Resend OTP email using EmailBuilder.
        """
        email_builder = EmailBuilder(first_name, recipient_email).build_resend_otp_email(otp)
        return self.send_email(email_builder)

    def send_welcome_email(self, first_name, recipient_email):
        """
        Send a welcome email using EmailBuilder.
        """
        email_builder = EmailBuilder(first_name, recipient_email).build_welcome_email()
        return self.send_email(email_builder)

    def send_forgot_password_otp(self, first_name, otp, recipient_email):
        """
        Send OTP email for password recovery using EmailBuilder.
        """
        email_builder = EmailBuilder(first_name, recipient_email).build_forgot_password_otp_email(otp)
        return self.send_email(email_builder)

    def send_bot_status_notification(self, bot_name, recipient_email, new_status):
        """
        Send Bot Status Change Notification to User.
        """
        email_builder = EmailBuilder(first_name="", recipient_email=recipient_email).build_handle_bot_status_change(bot_name, new_status)
        return self.send_email(email_builder)

    def send_custom_email(self, subject, html, recipient_email, body=None, attachments=None):
        """
        Send a custom email using EmailBuilder.
        """
        email_builder = EmailBuilder(first_name='', recipient_email=recipient_email) \
            .set_custom_email(subject, html)
        
        if body:
            email_builder.set_body(body)
        if attachments:
            email_builder.add_attachments(attachments)
        
        return self.send_email(email_builder)
