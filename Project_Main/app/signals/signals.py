from flask import current_app, g
from flask_mail import Message
from flask.signals import Namespace

signals = Namespace()

# Define custom signals
bot_status_changed = signals.signal('bot-status-changed')
bot_deleted = signals.signal('bot-deleted')

# Listener for bot status change
@bot_status_changed.connect
def handle_bot_status_change(sender, **kwargs):
    user_email = kwargs['user_email']
    bot_name = kwargs['bot_name']
    new_status = kwargs['new_status']

    email_service = g.email_service
    email_service.send_bot_status_notification(bot_name, user_email, new_status)


# Listener for bot deletion
@bot_deleted.connect
def handle_bot_deletion(sender, **kwargs):
    user_email = kwargs['user_email']
    bot_name = kwargs['bot_name']

    # Send email notification for bot deletion
    with current_app.app_context():
        msg = Message('Bot Deleted',
                      sender='',
                      recipients=[user_email])
        msg.body = f'Your bot "{bot_name}" has been deleted.'
        current_app.extensions['mail'].send(msg)
