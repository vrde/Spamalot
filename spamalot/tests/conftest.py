import asyncore
from threading import Thread

import spamalot
import pkg_resources

import smtpd

force_reply_command = ''
force_reply_code = None

def force_reply(command='', code=None):
    global force_reply_command, force_reply_code
    force_reply_command = command
    force_reply_code = code

def monkey_patch_SMTPChannel():
    for cmd in ('HELO', 'NOOP', 'QUIT', 'MAIL', 'RCPT', 'RSET', 'DATA'):
        # we need a closure
        def meta(cmd, old_method):
            def meta_smtp(self, *args, **kwargs):
                global force_reply_command, force_reply_code
                if force_reply_command == cmd:
                    self.push(force_reply_code)
                else:
                    old_method(self, *args, **kwargs)
            return meta_smtp

        method_name = 'smtp_%s' % cmd
        old_method = getattr(smtpd.SMTPChannel, method_name)
        setattr(smtpd.SMTPChannel, method_name,
            meta(cmd, old_method))

class SMTPTestServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data):
        self.last_peer = peer
        self.last_mailfrom = mailfrom
        self.last_rcpttos = rcpttos
        self.last_data = data
        print '*' * 80
        print mailfrom
        print
        print rcpttos
        print
        print data
        print '*' * 80

    def start(self):
        def run():
            asyncore.loop()

        t = Thread(target=run)
        t.daemon = True
        t.start()

    def stop(self):
        self.close()

smtp_test_server = None

def pytest_configure(config):
    monkey_patch_SMTPChannel()

    global smtp_test_server
    smtp_test_server = SMTPTestServer(('localhost', 2525), None)
    smtp_test_server.start()

    config = pkg_resources.resource_filename('spamalot.tests', 'test.ini')
    spamalot.init_mailer(config)

def pytest_runtest_setup(item):
    pass

def pytest_runtest_teardown(item):
    pass
    #smtp_test_server.stop()

def pytest_funcarg__server(request):
    return smtp_test_server

def pytest_funcarg__force_reply(request):
    force_reply()
    return force_reply

def pytest_funcarg__mailer(request):
    return spamalot.Mailer()

