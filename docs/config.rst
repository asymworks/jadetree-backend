.. currentmodule:: settings

Configuration
=============

The Jade Tree application server accepts several configuration keys to control
aspects of the server operation. Configuration keys may be specified in
multiple ways. The default values are set by the :mod:`jadetree.settings`
module, and are mostly undefined.

Default values are overridden by values in the following order:

* A Python file path provided in the ``JADETREE_CONFIG`` environment variable
  Note that the file path is relative to the :mod:`jadetree` module.
* Environment variables for each configuration key, with the name prefixed
  by ``JADETREE_`` (so to override the ``DB_URI`` configuration value, the
  environment variable is named ``JADETREE_DB_URI``).
* A configuration dictionary object passed to :func:`jadetree.create_app`

Configuration Keys
------------------

A list of configuration samples currently understood by Jade Tree:

+---------------------------+-------------------------------------------------+
| ``APP_SESSION_KEY``       | The encryption key used for browser session     |
|                           | data. This should be a random character string  |
|                           | and not published (i.e. provided as an          |
|                           | environment variable or with a private          |
|                           | configuration file in ``JADETREE_CONFIG``)      |
+---------------------------+-------------------------------------------------+
| ``APP_TOKEN_KEY``         | The key used to generate encrypted tokens for   |
|                           | registration confirmations and other            |
|                           | authentication purposes. This should be a       |
|                           | random character string and not published (i.e. |
|                           | provided as an environment variable or with a   |
|                           | private configuration file). See also           |
|                           | :mod:`itsdangerous.url_safe`                    |
+---------------------------+-------------------------------------------------+
| ``APP_TOKEN_SALT``        | The salt used to generate encrypted tokens for  |
|                           | registration confirmations and other            |
|                           | authentication purposes. This should be a       |
|                           | random character string and not published (i.e. |
|                           | provided as an environment variable or with a   |
|                           | private configuration file). See also           |
|                           | :mod:`itsdangerous.url_safe`                    |
+---------------------------+-------------------------------------------------+
| ``DB_URI``                | Database URI to be passed directly to           |
|                           | `Flask-SQLalchemy`_. This will override the     |
|                           | other ``DB_*`` keys.  Examples:                 |
|                           |                                                 |
|                           | - ``sqlite:///data/jadetree.db``                |
|                           | - ``mysql://user:pw@server:port/jadetree``      |
+---------------------------+-------------------------------------------------+
| ``DB_DRIVER``             | Database Driver string (``sqlite``, ``mysql``,  |
|                           | ``postgresql``, or any other driver/dialect     |
|                           | string supported by `SQLalchemy`_.              |
+---------------------------+-------------------------------------------------+
| ``DB_FILE``               | Database File Name, only applicable for         |
|                           | ``sqlite`` databases. Use with other database   |
|                           | drivers will throw an exception.                |
+---------------------------+-------------------------------------------------+
| ``DB_USERNAME``           | Database connection username.                   |
+---------------------------+-------------------------------------------------+
| ``DB_PASSWORD``           | Database connection password.                   |
+---------------------------+-------------------------------------------------+
| ``DB_HOST``               | Database connection hostname.                   |
+---------------------------+-------------------------------------------------+
| ``DB_PORT``               | Database connection port (defaults to 3306 for  |
|                           | MySQL and 5432 for PostgreSQL).                 |
+---------------------------+-------------------------------------------------+
| ``DB_NAME``               | Database name.                                  |
+---------------------------+-------------------------------------------------+
| ``MAIL_SERVER``           | SMTP server hostname or address used to send    |
|                           | system email messages.                          |
+---------------------------+-------------------------------------------------+
| ``MAIL_PORT``             | SMTP server port (defaults to ``25`` if the     |
|                           | ``MAIL_USE_TLS`` setting is false or not set,   |
|                           | otherwise defaults to ``587``).                 |
+---------------------------+-------------------------------------------------+
| ``MAIL_USE_TLS``          | Boolean to use ``STARTTLS`` to encrypt SMTP     |
|                           | server connections.                             |
+---------------------------+-------------------------------------------------+
| ``MAIL_USERNAME``         | SMTP server username or ``None``.               |
+---------------------------+-------------------------------------------------+
| ``MAIL_PASSWORD``         | SMTP server password or ``None``.               |
+---------------------------+-------------------------------------------------+
| ``MAIL_SENDER``           | Sender address for system email messages,       |
|                           | usually an administrator account like           |
|                           | ``info@jadetree.io`` or an unmonitored mailbox  |
|                           | like ``do-not-reply@jadetree.io``.              |
+---------------------------+-------------------------------------------------+
| ``LOGGING_DEST``          | Default destination for server log messages,    |
|                           | can be set to ``wsgi`` (default), ``stdout``,   |
|                           | or ``stderr``. The default ``wsgi`` setting     |
|                           | uses the default Flask approach of sending      |
|                           | messages to the ``wsgi_error_stream`` which is  |
|                           | defined by the WSGI server (typically stderr).  |
+---------------------------+-------------------------------------------------+
| ``LOGGING_LEVEL``         | Sets the global logging level for the server,   |
|                           | and can be set as a Python                      |
|                           | :ref:`Logging Level <python:levels>` string or  |
|                           | numeric value. Syslog severity keywords such as |
|                           | ``err`` or ``crit`` may also be specifie and    |
|                           | will be mapped to the closest Python level.     |
+---------------------------+-------------------------------------------------+
| ``LOGGING_FORMAT``        | Formatter string to be used for server log      |
|                           | messages sent to the console or WSGI stream.    |
+---------------------------+-------------------------------------------------+
| ``LOGGING_BACKTRACE``     | Boolean to control whether stack traces are     |
|                           | included in log messages. The default is False, |
|                           | which suppresses backtraces; however, email     |
|                           | log messages will still contain backtraces.     |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL``             | Boolean to control whether log messages are     |
|                           | sent to server administrators via email. This   |
|                           | is only used in Production mode, and the level  |
|                           | should be set to ``ERROR`` to limit the number  |
|                           | of emails sent.                                 |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL_LEVEL``       | Level of log messages which are emailed to the  |
|                           | server administrators. By default this is set   |
|                           | to ``ERROR`` so that only the most critical log |
|                           | messages are sent.                              |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL_ADMINS``      | Email address or list of addresses which should |
|                           | receive log messages.                           |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL_SUBJECT``     | Email subject for log messages. Defaults to     |
|                           | "[Jade Tree] Production Site Error".            |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL_BODY_TMPL``   | Template path to be formatted into the plain    |
|                           | text body of the log email. Defaults to         |
|                           | ``email/text/adm-error.text.j2``.               |
+---------------------------+-------------------------------------------------+
| ``LOG_EMAIL_HTML_TMPL``   | Template path to be formatted into the HTML     |
|                           | body of the log email. Defaults to              |
|                           | ``email/html/adm-error.html.j2``.               |
+---------------------------+-------------------------------------------------+
| ``DEFAULT_LOCALE``        | Default locale string to load for localized     |
|                           | string formatting operations (dates, numbers,   |
|                           | and currencies). Defaults to ``en_US``.         |
+---------------------------+-------------------------------------------------+
| ``DEFAULT_CURRENCY``      | Default ISO 4166 currency code for the global   |
|                           | server installation. Defaults to ``USD``.       |
+---------------------------+-------------------------------------------------+

.. _Flask-Sqlalchemy: https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/#connection-uri-format
.. _SQLalchemy: https://docs.sqlalchemy.org/en/13/core/engines.html

Database Connection Setup
-------------------------

The Jade Tree database connection can be specified as a single URI which is
passed directly to `Flask-SQLalchemy`_, or with individual configuration keys
to specify driver, hostname, database, etc. The individual keys are used to
construct a Database URI as in the following template:

``{DB_DRIVER}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}``

.. important::
  Jade Tree requires that all URI portions are URL-escaped when the ``DB_URI``
  configuration key is used.  When the individual configuration keys are
  provided, the ``DB_USERNAME`` and ``DB_PASSWORD`` values are escaped by Jade
  Tree prior to being passed to SQLalchemy.

Mail Server Setup
-----------------

Jade Tree sends emails to users and site administrators in response to events
happening on the server, so configuring an SMTP server is critical for proper
server operation. Internally Jade Tree uses the :mod:`Flask-Mail <flask-mail>`
library, and specifics about the configuration can be found at that site.

Basic setup using an internal forwarding SMTP server only requires that the
``MAIL_SERVER`` and ``MAIL_SENDER`` values are set appropriately, which will
instruct Jade Tree to use unencrypted SMTP without any authentication.

.. warning::
  Only use this if you have a properly configured SMTP forwarder on your
  network. Messages sent through public SMTP relays may be flagged as spam by
  email providers.

A more typical setup might use a public mail hosting service such as Google
Mail, which requires third party applications to log in with a username and
password with a secured connection. The complete configuration would look
similar to the below snippet::

  MAIL_SERVER = 'smtp.gmail.com'
  MAIL_PORT = 587
  MAIL_USE_TLS = True
  MAIL_USERNAME = '<user>@gmail.com'
  MAIL_PASSWORD = 'your_gmail_password'

.. important::
  Jade Tree and Flask-Mail require a plaintext password to authenticate with
  Google Mail and other third-party mail providers. To keep your password safe,
  take care that the Jade Tree configuration file has the appropriate file
  permissions (readable only by the root user) and is located outside the web
  server's document root so that it cannot be inadvertently served to a user.

For Google Mail specifically, we also recommend setting up an `App Password`_
for Jade Tree so that your main password is never used in the configuration
file, and if it is ever compromised, the App Password can be revoked without
affecting your Google Mail account or any other apps.  The setup for that is
very similar to the above, just using the app password in place of your email
password::

  MAIL_SERVER = 'smtp.gmail.com'
  MAIL_PORT = 587
  MAIL_USE_TLS = True
  MAIL_USERNAME = '<user>@gmail.com'
  MAIL_PASSWORD = 'abcdefghijklmnop'

.. _`App Password`: https://support.google.com/accounts/answer/185833?hl=en


Server Logging Setup
--------------------

Jade Tree uses the Flask logging facilities, which internally rely on the
Python :mod:`Logging <python:library.logging>` backend for all server logging.
Jade Tree does override some of Flask's configuration so that the setup can be
customized for individual applications.

The main logging destination is set with the ``LOGGING_DEST`` setting. By
default, log messages are sent to the WSGI Error Stream for handling by the
WSGI server. Typically this will be printed to the ``stderr`` console, but
could also be set up for logging to file or another backend. This can be
overridden by setting the ``LOGGING_DEST`` setting to either ``stdout`` or
``stderr``, which directs log messages to the console directly.

.. warning::
  Setting ``LOGGING_DEST`` to a value other than ``wsgi`` means that log
  messages are no longer sent to the WSGI server at all. Users should be aware
  that this does not mirror messages, but redirects them completely.

Further customization of logging happens with the ``LOGGING_LEVEL`` and
``LOGGING_FORMAT`` settings. Setting the ``LOGGING_LEVEL`` to either a string
corresponding to a Python :ref:`Logging Level <python:levels>` or a Syslog
Severity code will inhibit logging messages with lower severity.

Recognized values for ``LOGGING_LEVEL`` are (all are case insensitive):

+---------------+-------------------------+
| Keywords      | Equivalent Python Level |
+===============+=========================+
| ``panic``     | ``CRITICAL``            |
| ``alert``     |                         |
| ``critical``  |                         |
| ``crit``      |                         |
+---------------+-------------------------+
| ``error``     | ``ERROR``               |
| ``err``       |                         |
+---------------+-------------------------+
| ``warning``   | ``WARNING``             |
| ``warn``      |                         |
+---------------+-------------------------+
| ``notice``    | ``INFO``                |
| ``info``      |                         |
+---------------+-------------------------+
| ``debug``     | ``DEBUG``               |
+---------------+-------------------------+

.. warning::
  The ``LOGGING_LEVEL`` configuration value sets the global level for the root
  logger, and is effectively a lower limit on the log messages processed by
  all handlers.  Take care to set this correctly, especially if using the
  email logging function, as if the ``LOGGING_LEVEL`` is set higher than the
  ``LOG_EMAIL_LEVEL``, no emails will be sent.

Log message formatting is controlled by the ``LOGGING_FORMAT`` setting, and
defaults to ``[%(asctime)s] %(levelname)s in %(module)s: %(message)s``. Jade
Tree will inject additional :class:`~flask.Request` object information into
log records if available, making it available for use in format strings. New
request variables available are:

+-----------------+---------------------------------------------------------+
| Attribute       | Value                                                   |
+=================+=========================================================+
| ``request``     | Complete :class:`~flask.Request` object                 |
+-----------------+---------------------------------------------------------+
| ``remote_addr`` | :attr:`Request.remote_addr <flask.Request.remote_addr>` |
+-----------------+---------------------------------------------------------+
| ``url``         | :attr:`Request.url <flask.Request.url>`                 |
+-----------------+---------------------------------------------------------+

Stack backtrace reporting is suppressed by default by Jade Tree for log
messages sent to the WSGI error stream. This behavior can be reverted to the
standard Python behavior by setting ``LOGGING_BACKTRACE`` to ``True``.

In addition to WSGI and console reporting, Jade Tree supports sending email
alerts to system administrators when high severity log messages are recorded
in production mode (this function is disabled by default in development mode).
To enable email reporting, set the ``LOG_EMAIL`` setting to True and set the
``LOG_EMAIL_`` settings::

  LOG_EMAIL = True
  LOG_EMAIL_LEVEL = 'error'
  LOG_EMAIL_ADMINS = ['admin@your-site.com']
  LOG_EMAIL_SUBJECT = '[Jade Tree] Production Site Error'
  LOG_EMAIL_BODY_TMPL = 'email/text/adm-error.text.j2'
  LOG_EMAIL_HTML_TMPL = 'email/html/adm-error.html.j2'

The email is generated using Jinja2 templates rendered with the default Flask
:func:`~Flask.render_template` function. Special variables available within
the template are given in the table below:

+-----------------------+---------------------------------------------------+
| Template Variable     | Value                                             |
+=======================+===================================================+
| ``record``            | Complete :class:`~logging.LogRecord` object       |
+-----------------------+---------------------------------------------------+
| ``request``           | Complete :class:`~flask.Request` object           |
+-----------------------+---------------------------------------------------+
| ``formatted_record``  | Formatted log message                             |
+-----------------------+---------------------------------------------------+
| ``exc_class``         | Python :class:`python:Exception` subclass name    |
+-----------------------+---------------------------------------------------+
| ``exc_msg``           | Python :class:`python:Exception` message          |
+-----------------------+---------------------------------------------------+
| ``stack_trace``       | Backtrace as retrieved from :func:`sys.exc_info`  |
|                       | and extracted with :func:`traceback.extract_tb`.  |
+-----------------------+---------------------------------------------------+

The stack backtrace is a collection of stack entries, and can be rendered by
a template similar to this (taken from ``email/text/adm-error.text.j2``):

.. code-block:: jinja

  {% if stack_trace %}
  A stack trace for the exception is below:
  -----------------------------------------
  {% for trace in stack_trace %}
  File "{{ trace.filename }}", line {{ trace.lineno }}, in {{ trace.name }}
    {{ trace.line }}

  {% endfor %}
  {% endif %}

Default Configuration Values
----------------------------

TBD
