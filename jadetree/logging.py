# =============================================================================
#
# Jade Tree Personal Budgeting Application | jadetree.io
# Copyright (c) 2020 Asymworks, LLC.  All Rights Reserved.
#
# =============================================================================

import logging
import sys
import traceback

from flask import has_request_context, render_template, request
from flask.logging import default_handler, wsgi_errors_stream
from flask_mail import Message

from jadetree.exc import ConfigError
from jadetree.mail import mail

__all__ = (
    'MailHandler',
    'NoTraceFormatter',
    'RequestFormatter',
    'init_logging',
)

LEVELS = {
    'PANIC':        logging.CRITICAL,               # noqa: E241
    'ALERT':        logging.CRITICAL,               # noqa: E241
    'CRITICAL':     logging.CRITICAL,               # noqa: E241
    'CRIT':         logging.CRITICAL,               # noqa: E241
    'ERROR':        logging.ERROR,                  # noqa: E241
    'ERR':          logging.ERROR,                  # noqa: E241
    'WARNING':      logging.WARNING,                # noqa: E241
    'WARN':         logging.WARNING,                # noqa: E241
    'NOTICE':       logging.INFO,                   # noqa: E241
    'INFO':         logging.INFO,                   # noqa: E241
    'DEBUG':        logging.DEBUG,                  # noqa: E241
}


def lookup_level(level):
    '''Lookup a Logging Level by Python Name or syslog Name'''
    if isinstance(level, int):
        return level
    return LEVELS.get(str(level).upper(), logging.NOTSET)


class MailHandler(logging.Handler):
    '''
    Custom Log Handler class which acts like :class:`logging.SMTPHandler` but
    uses :mod:`flask_mail` and :func:`flask.render_template` on the back end
    to send Jinja templated HTML messages. The :obj:`jadetree.mail.mail`
    object must be available and initialized, so this handler should not be
    used prior to calling :meth:`flask_mail.Mail.init_app`.
    '''
    def __init__(self, sender, recipients, subject, text_template=None,
                 html_template=None, **kwargs):
        '''
        Initialize the Handler.

        Initialize the instance with the sender, recipient list, and subject
        for the email.  To use Jinja templates, pass a template path to the
        ``text_template`` and ``html_template`` parameters.  The templates
        will be called with the following context items set:

        .. data:: record
            :type: :class:`python:logging.LogRecord`

            Log Record which was sent to the logger

        .. data:: formatted_record
            :type: str

            Formatted log record from :meth:`python:logging.Handler.format`

        .. data:: request
            :type: :class:`flask.Request`

            Flask request object (or None if not available)

        .. data:: user
            :type: :class:`jadetree.models.User`

            User object (or :class:`flask_login.AnonymousUserMixin`)

        Additional template context variables may be passed to the handler
        constructor as keyword arguments.

        :param sender: Email sender address
        :type sender: str
        :param recipients: Email recipient addresses
        :type recipients: str or list
        :param subject: Email subject
        :type subject: str
        :param text_template: Path to Jinja2 Template for plain-text message
        :type text_template: str
        :param html_template: Path to Jinja2 Template for HTML message
        :type html_template: str
        :param kwargs: Additional variables to pass to templates
        :type kwargs: dict
        '''
        super(MailHandler, self).__init__()
        self.sender = sender
        if isinstance(recipients, str):
            recipients = [recipients]
        self.recipients = recipients
        self.subject = subject
        self.text_template = text_template
        self.html_template = html_template
        self.template_context = kwargs

    def getSubject(self):
        '''
        Determine the subject for the email. If you want to override the
        subject line with something record-dependent, override this method.
        '''
        return self.subject

    def emit(self, record):
        '''Format the record and send it to the specified recipients'''
        try:
            request_obj = None
            if has_request_context():
                request_obj = request

            # Load stack trace (if an exception is being processed)
            exc_type, exc_msg, stack_trace = sys.exc_info()

            # Format Record
            formatted_record = self.format(record)
            text_body = formatted_record
            html_body = None

            # Render Text Body
            if self.text_template is not None:
                text_body = render_template(
                    self.text_template,
                    record=record,
                    request=request_obj,
                    formatted_record=formatted_record,
                    exc_class='None' if not exc_type else exc_type.__name__,
                    exc_msg=exc_msg,
                    stack_trace=traceback.extract_tb(stack_trace),
                    **self.template_context,
                )

            # Render HTML Body
            if self.html_template is not None:
                html_body = render_template(
                    self.html_template,
                    record=record,
                    request=request_obj,
                    formatted_record=formatted_record,
                    exc_class='None' if not exc_type else exc_type.__name__,
                    exc_msg=exc_msg,
                    stack_trace=traceback.extract_tb(stack_trace),
                    **self.template_context,
                )

            # Send the message with Flask-Mail
            msg = Message(
                self.getSubject(),
                sender=self.sender,
                recipients=self.recipients,
            )
            msg.body = text_body
            msg.html = html_body

            mail.send(msg)

        except Exception:       # pragma: no cover
            self.handleError(record)


class RequestInjectorMixin(object):
    '''
    Inject the Flask :attr:`flask.Flask.request` object into the logger record
    as well as shortcut getters for :attr:`flask.Request.url` and
    :attr:`flask.Request.remote_addr`
    '''
    def _injectRequest(self, record):
        if has_request_context():
            record.request = request
            record.remote_addr = request.remote_addr
            record.url = request.url
        else:
            record.request = None
            record.remote_addr = None
            record.url = None

        return record


class NoTraceFormatter(logging.Formatter, RequestInjectorMixin):
    '''
    Custom Log Formatter which suppresses automatic printing of stack trace
    information even when :attr:`python:logging.LogRecord.exc_info` is set.
    This wholly overrides :meth:`python:logging.Formatter.format`.

    The Flask :class:`~flask.Flask.Request` object is also included into the
    logger record as well as shortcut getters for :attr:`flask.Request.url`
    and :attr:`flask.Request.remote_addr`
    '''
    def format(self, record):
        '''
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a string
        formatting operation which yields the returned string. Before
        formatting the dictionary, a couple of preparatory steps are carried
        out.  The message attribute of the record is computed using
        :meth:`python:logging.LogRecord.getMessage`.  If the formatting string
        uses the time (as determined by a call to
        :meth:`python:logging.LogRecord.usesTime`),
        :meth:`python:logging.LogRecord.formatTime` is called to format the
        event time.
        '''
        record = self._injectRequest(record)
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        return self.formatMessage(record)


class RequestFormatter(logging.Formatter, RequestInjectorMixin):
    '''
    Custom Log Formatter which includes the Flask :attr:`flask.Flask.request`
    object into the logger record as well as shortcut getters for
    :attr:`flask.Request.url` and :attr:`flask.Request.remote_addr`
    '''
    def format(self, record):
        '''
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a string
        formatting operation which yields the returned string. Before
        formatting the dictionary, a couple of preparatory steps are carried
        out.  The message attribute of the record is computed using
        :meth:`python:logging.LogRecord.getMessage`.  If the formatting string
        uses the time (as determined by a call to
        :meth:`python:logging.LogRecord.usesTime`),
        :meth:`python:logging.LogRecord.formatTime` is called to format the
        event time.
        '''
        record = self._injectRequest(record)
        return super(RequestFormatter, self).format(record)


def init_email_logger(app, root_logger):
    '''Install the Email Log Handler to the Root Logger'''
    for k in ('MAIL_SERVER', 'MAIL_SENDER', 'LOG_EMAIL_ADMINS',
              'LOG_EMAIL_SUBJECT'):
        if k not in app.config:
            raise ConfigError(
                '{} must be defined in the application configuration in '
                'order to send logs to an email recipient.'.format(k),
                config_key=k
            )

    mail_handler = MailHandler(
        sender=app.config.get('MAIL_SENDER', None),
        recipients=app.config['LOG_EMAIL_ADMINS'],
        subject=app.config['LOG_EMAIL_SUBJECT'],
        text_template=app.config.get('LOG_EMAIL_BODY_TMPL', None),
        html_template=app.config.get('LOG_EMAIL_HTML_TMPL', None),
    )
    mail_handler.setLevel(
        lookup_level(app.config.get('LOG_EMAIL_LEVEL', logging.ERROR))
    )
    mail_handler.setFormatter(NoTraceFormatter(
        app.config.get('LOG_EMAIL_FORMAT', None)
    ))
    root_logger.addHandler(mail_handler)

    # Dump Logger Configuration to Debug
    app.logger.debug('Installed Email Log Handler')
    app.logger.debug(
        'Email Log Recipients: %s', ', '.join(mail_handler.recipients)
    )
    app.logger.debug('Email Log Subject: %s', mail_handler.subject)
    app.logger.debug(
        'Email Log Templates: %s, %s',
        mail_handler.text_template,
        mail_handler.html_template,
    )


def init_logging(app):
    '''
    This sets up the application logging infrastructure, including console or
    WSGI server logging as well as email logging for production server errors.
    '''
    logging_dest = app.config.get('LOGGING_DEST', 'wsgi').lower()
    logging_stream = wsgi_errors_stream
    if logging_dest == 'stdout':
        logging_stream = sys.stdout
    elif logging_dest == 'stderr':
        logging_stream = sys.stderr
    elif logging_dest != 'wsgi':
        raise ConfigError(
            'LOGGING_DEST must be set to wsgi, stdout, or stderr (is set '
            'to {})'.format(logging_dest)
            , config_key='LOGGING_DEST'
        )

    logging_level = lookup_level(app.config.get('LOGGING_LEVEL', None))
    logging_format = app.config.get('LOGGING_FORMAT', None)
    logging_backtrace = app.config.get('LOGGING_BACKTRACE', True)
    if not isinstance(logging_backtrace, bool):
        raise ConfigError(
            'LOGGING_BACKTRACE must be a boolean value, found {}'
            .format(type(logging_backtrace).__name__),
            config_key='LOGGING_BACKTRACE'
        )

    fmt_class = RequestFormatter if logging_backtrace else NoTraceFormatter

    app_handler = logging.StreamHandler(logging_stream)
    app_handler.setFormatter(fmt_class(logging_format))
    app_handler.setLevel(logging_level)

    # Install Log Handler and Formatter on Flask Logger
    app.logger.setLevel(logging_level)
    app.logger.addHandler(app_handler)

    # Remove Flask Default Log Handler
    app.logger.removeHandler(default_handler)

    # Notify Logging Initialized
    app.logger.debug('Logging Boostrapped')
    app.logger.debug('Installed %s Log Handler', logging_dest)

    # Setup the Mail Log Handler if configured
    if not app.debug or app.config.get('DBG_FORCE_LOGGERS', False):
        if app.config.get('LOG_EMAIL', False):
            init_email_logger(app, app.logger)
