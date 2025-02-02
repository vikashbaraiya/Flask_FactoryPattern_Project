from app.EmailConfig.EmailTemplate import EmailTemplate

class EmailBuilder:
    def __init__(self, first_name, recipient_email):
        self.first_name = first_name
        self.recipient_email = recipient_email
        self.subject = ""
        self.html = ""
        self.body = None
        self.attachments = None

    def build_otp_email(self, otp):
        self.subject = "Your OTP Code"
        self.html = EmailTemplate.generate_otp_template(self.first_name, otp)
        return self

    def build_resend_otp_email(self, otp):
        self.subject = "Resend Your OTP Code"
        self.html = EmailTemplate.generate_resend_otp_template(self.first_name, otp)
        return self

    def build_welcome_email(self):
        self.subject = "Welcome to Cognitiv.AI!"
        self.html = EmailTemplate.generate_welcome_template(self.first_name)
        return self

    def build_forgot_password_otp_email(self, otp):
        self.subject = "Your OTP Code"
        self.html = EmailTemplate.generate_otp_forgot_password(self.first_name, otp)
        return self
    
    def build_handle_bot_status_change(self, bot_name, new_status):
        self.subject = "Bot Status Changed"
        self.html = EmailTemplate.generate_bot_status_change_email(bot_name, new_status)
        return self

    def set_custom_email(self, subject, html):
        self.subject = subject
        self.html = html
        return self

    def set_body(self, body):
        self.body = body
        return self

    def add_attachments(self, attachments):
        self.attachments = attachments
        return self

    def get_email_content(self):
        return {
            'subject': self.subject,
            'html': self.html,
            'body': self.body,
            'attachments': self.attachments,
        }
