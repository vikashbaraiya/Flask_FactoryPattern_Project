
class EmailTemplate:

    @staticmethod
    def generate_otp_template(first_name, otp):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your OTP Code</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
                .otp {{ display: inline-block; margin: 20px 0; padding: 10px 15px; font-size: 24px; font-weight: bold; background-color: #e0f7fa; border: 1px solid #0097a7; border-radius: 5px; color: #00796b; }}
                .footer {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome, {first_name}!</h1>
                <p>Thank you for signing up! To complete your registration, please use the following One-Time Password (OTP):</p>
                <div class="otp">{otp}</div>
                <p>This code is valid for the next 5 minute. Please enter it on our website to complete your verification.</p>
                <p>If you didn’t request this code, please ignore this email.</p>
                <div class="footer">
                    Thank you for joining us!<br>
                    <small>This is a bot-generated email, please do not reply. Replies will not be read, as this email address is used for notifications only.</small>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def generate_resend_otp_template(first_name, otp):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Resend Your OTP Code</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
                .otp {{ display: inline-block; margin: 20px 0; padding: 10px 15px; font-size: 24px; font-weight: bold; background-color: #ffe0b2; border: 1px solid #ff9800; border-radius: 5px; color: #e65100; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hello again, {first_name}!</h1>
                <p>We received a request to resend your One-Time Password (OTP). Please use the following code:</p>
                <div class="otp">{otp}</div>
                <p>This code is valid for the next 5 minute. Please enter it on our website to complete your verification.</p>
                <p>If you didn’t request this code, please ignore this email.</p>
                <div class="footer">
                    Thank you for joining us!<br>
                    <small>This is a bot-generated email, please do not reply. Replies will not be read, as this email address is used for notifications only.</small>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_welcome_template(first_name):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to Cogntiv.AI!</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
                .footer {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome to Cognitiv.AI, {first_name}!</h1>
                <p>We’re excited to have you join our community of forward-thinkers. To get started, log in to your account and explore the innovative features designed to elevate your experience.</p>
                <div class="footer">
                    Best regards,<br>
                    The Cogntiv.AI Team<br>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_otp_forgot_password(first_name,otp):
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your OTP Code</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
                .otp {{ display: inline-block; margin: 20px 0; padding: 10px 15px; font-size: 24px; font-weight: bold; background-color: #e0f7fa; border: 1px solid #0097a7; border-radius: 5px; color: #00796b; }}
                .footer {{ margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Hello, {first_name}</h1>
                <p>To reset your password, please use the following One-Time Password (OTP):</p>
                <div class="otp">{otp}</div>
                <p>This code is valid for the next 5 minutes. Please enter it to proceed with resetting your password.</p>
                <p>If you didn’t request this code, please ignore this email.</p>
                <div class="footer">
                    Thank you for using our service!<br>
                    <small>This is a bot-generated email, please do not reply. Replies will not be read, as this email address is used for notifications only.</small>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def generate_bot_status_change_email(bot_name, new_status):
        """
        Generate an HTML email template for bot status change notification.
        """
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bot Status Update</title>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 8px; }}
                .header {{ font-size: 20px; font-weight: bold; color: #00796b; margin-bottom: 20px; }}
                .content {{ font-size: 16px; line-height: 1.5; color: #333; }}
                .bot-name {{ font-weight: bold; color: #0097a7; }}
                .status {{ font-weight: bold; color: #d32f2f; }}
                .footer {{ margin-top: 20px; font-size: 14px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">Bot Status Notification</div>
                <div class="content">
                    <p>Hello,</p>
                    <p>The status of your bot <span class="bot-name">"{bot_name}"</span> has been changed to <span class="status">{new_status}</span>.</p>
                    <p>If you did not expect this change, please check your bot configuration or contact support.</p>
                </div>
                <div class="footer">
                    Thank you for using our service!<br>
                    <small>This is an automated email. Please do not reply directly to this email.</small>
                </div>
            </div>
        </body>
        </html>
        """