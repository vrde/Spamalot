import smtplib
import socket

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import email.Charset
# http://bytes.com/topic/python/answers/27012-problems-creating-mail-content-using-email-mimetext-non-ascii-encoding
email.Charset.add_charset('utf-8', email.Charset.SHORTEST, None, None)
import config

class NoMoreAttemptsException(Exception): pass

class Message(object):
    '''Represent a message to send'''

    def __init__(self, recipient, subject, plain, html=None, sender=None, encoding=None):
        '''Create a new message.

        recipient -- the recipient
        subject -- the subject
        plain -- the plain message
        html -- the html message (default is None)
        sender -- the sender of the email (if None -as the default-
                  sender is set to the config value.'''

        self.sender = sender or config.conf['mailer']['sender']
        self.recipient = recipient
        self.subject = subject 
        self.encoding = encoding or config.conf['mailer']['encoding']

        # XXX: mmm
        if isinstance(plain, unicode) and self.encoding.lower() == 'utf-8':
            plain = plain.encode('utf-8')
        if isinstance(html, unicode) and self.encoding.lower() == 'utf-8':
            html = html.encode('utf-8')

        self.plain = plain
        self.html = html
    
    def as_string(self):
        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = Header(self.subject, self.encoding)
        # FIXME: sender and recipient must be decoded like the subject?
        msg['From'] = self.sender
        msg['To'] = self.recipient

        plain_part = MIMEText(self.plain, 'plain', self.encoding)
        msg.attach(plain_part)

        if self.html:
            html_part = MIMEText(self.html, 'html', self.encoding)
            msg.attach(html_part)

        return msg.as_string()

class Mailer(object):
    '''Email sender.'''

    def __init__(self, batch=False):
        '''Constructor.
        
        Batch is used for auto-connecto/disconnect, if batch is False
        (default) the Mailer disconnect after the .send(), if it is True
        it will not disconnect.
        
        Batch mode avoids to disconnect after every single sending.'''

        self.connected = False
        self.batch = batch

    def _connect(self):
        '''Connect to the SMTP server.'''

        if self.connected:
            return

        smtpserver = config.conf['mailer']['host']
        smtpport = config.conf['mailer']['port']
        username = config.conf['mailer']['username']
        password = config.conf['mailer']['password']
        timeout = config.conf['mailer']['timeout']

        try:
            self.connection = smtplib.SMTP(smtpserver, smtpport, timeout=timeout)
            if username and password:
                config.log.debug('using username and password')
                self.connection.login(username, password)
            config.log.debug('connected to %s' % smtpserver)
            self.connected = True

        except smtplib.SMTPHeloError, e:
            config.log.critical('Helo Error %s', e)
            raise
        except smtplib.SMTPAuthenticationError, e:
            config.log.critical('Wrong username and/or password')
            raise
        except smtplib.SMTPConnectError, e:
            config.log.critical('Connection error: %s' % e)
            raise
        except smtplib.SMTPException, e:
            config.log.critical('General Error: %s' % e)
            raise
        except socket.timeout, e:
            config.log.critical('Connection timeout')
            raise

    def _disconnect(self):
        '''Disconnect to the SMTP server.'''

        smtpserver = config.conf['mailer']['host']
        self.connection.quit()
        config.log.debug('disconnected to %s' % smtpserver)
        self.connected = False

    def _send(self, message):
        try:
            config.log.debug('trying to email %s' % message.recipient)

            self.connection.sendmail(
                message.sender,
                message.recipient,
                message.as_string())

            config.log.info('message sent to %s' % message.recipient)
        except smtplib.SMTPServerDisconnected, e:
            config.log.warning('SMTP server disconnected: %s' % e)
            self.connected = False
            raise
        except smtplib.SMTPSenderRefused, e:
            config.log.critical('SMTP server refused the sender: %s' % e)
            raise
        except smtplib.SMTPRecipientsRefused, e:
            config.log.warning('SMTP server refused the recipient: %s' % e)
            raise
        except smtplib.SMTPDataError, e:
            config.log.critical('SMTP data error: %s' % e)
            raise
        except IOError, e:
            config.log.warning('I/O error: %s' % e)
            self.connected = False
            raise

    def send(self, message):
        '''Send a message.
        
        If the send fails*, this method will retry a fixed number of times
        (configured via the mailer.attempts value); if also the last attempt
        fails, 'send' raises a NoMoreAttemptsException.

        You should catch smtplib.SMTPRecipientsRefused and blacklist the refused
        recipients.
        
        * "fail" means 1) the server disconnected 2) an IOError occured
          3) a timeout occurred.'''

        left_attempts = config.conf['mailer']['attempts']

        while True:
            left_attempts -= 1
            try:
                self._connect()
                self._send(message)
                break
            except (smtplib.SMTPServerDisconnected, IOError, socket.timeout):
                config.log.debug('Email %s has failed, %s attempts left' %\
                    (left_attempts, message.recipient))
                if not left_attempts:
                    raise NoMoreAttemptsException()

        if not self.batch:
            self._disconnect()

    def failsafe_send(self, message):
        try:
            self.send(message)
            return True
        except Exception, e:
            config.log.critical(
                'FAILSAFE SEND FAILURE!\nException: %s\nMessage: %s' %\
                (e, message.as_string()))
        return False

def send(message):
    m = Mailer()
    m.send(message)

def failsafe_send(message):
    m = Mailer()
    return m.failsafe_send(message)

