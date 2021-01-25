"""Jade Tree Email Support.

Jade Tree Personal Budgeting Application | jadetree.io
Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
"""

from flask import current_app
from flask_mail import Mail, Message

from jadetree.exc import ConfigError

mail = Mail()

__all__ = ('init_mail', 'mail', 'send_email')


def init_mail(app):
    """Register the Flask-Mail object with the Application."""
    if not app.config.get('MAIL_ENABLED', False):
        app.logger.debug('Skipping mail setup (disabled)')
        return

    required_keys = (
        'MAIL_SERVER', 'MAIL_SENDER', 'SITE_ABUSE_MAILBOX', 'SITE_HELP_MAILBOX'
    )
    for k in required_keys:
        if k not in app.config:
            raise ConfigError(
                '{} must be defined in the application configuration'
                .format(k),
                config_key=k
            )

    mail.init_app(app)

    # Add Site Mailboxes to templates
    app.jinja_env.globals.update(
        site_abuse_mailbox=app.config['SITE_ABUSE_MAILBOX'],
        site_help_mailbox=app.config['SITE_HELP_MAILBOX'],
    )

    # Dump Configuration to Debug
    app.logger.debug(
        'Mail Initialized with server %s and sender %s',
        app.config['MAIL_SERVER'],
        app.config['MAIL_SENDER'],
    )


def send_email(subject, recipients, body, html=None, sender=None):
    """Send an Email Message using Flask-Mail."""
    recip_list = [recipients] if isinstance(recipients, str) else recipients

    if not current_app.config.get('MAIL_ENABLED', False):
        current_app.logger.debug(
            'Skipping send_email({}) to {} (email disabled)'.format(
                subject,
                ', '.join(recip_list)
            )
        )
        return

    if sender is None:
        sender = current_app.config['MAIL_SENDER']

    msg = Message(subject, sender=sender, recipients=recip_list)
    msg.body = body
    msg.html = html
    mail.send(msg)
