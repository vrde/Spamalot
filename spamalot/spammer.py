#!/usr/bin/python

import smtplib
import codecs
import time
import logging
from string import Template

import config
import spamalot
from spamalot import utils


class Spammer(object):
    '''
    attributes:
        recipients  -- a dict with all the data of the recipients;
        all_addrs   -- the set of all addresses loaded;
        left_addrs  -- the set of the left addresses to email;
        sent_addrs  -- the set of addresses e-mailed;
        black_addrs -- the set of blacklisted addresses;
    '''

    def __init__(self, mailer):
        self.log = logging.getLogger('spammer')
        self.file_encoding = config.conf['spammer']['file_encoding']
        self._parse_message()
        self._parse_recipients()
        self._parse_sent()
        self._parse_blacklist()
        self.mailer = mailer

    @property
    def left_addrs(self):
        return self.all_addrs - (self.sent_addrs | self.black_addrs)

    def _prepare_message(self, recipient):
        message = spamalot.Message(
            recipient['email'],
            # FIXME: check encoding
            config.conf['spammer']['subject'],
            self.plain_email_template.substitute(recipient),
            self.html_email_template.substitute(recipient),
        )
        return message

    def _parse_message(self):
        '''Parse the text and html messages to send.'''

        plain = config.conf['spammer']['plain_message']
        html = config.conf['spammer']['html_message']

        self.plain_email_template = Template(codecs.open(
            plain, 'r', self.file_encoding).read())

        self.html_email_template = Template(codecs.open(
            html, 'r', self.file_encoding).read())

        self.log.debug('loaded plain and html messages')

    def _parse_recipients(self):
        '''Parse the csv file.'''

        filename = config.conf['spammer']['recipients']
        reader = utils.UnicodeCSVDictReader(
            open(filename, 'rb'), self.file_encoding)

        self.recipients = []
        self.all_addrs = set()

        for line in reader:
            self.recipients.append(line)
            self.all_addrs.add(line['email'])

        self.log.debug('loaded %d recipients' % len(self.recipients))

    def _parse_sent(self):
        '''Parse the list of sent email.'''

        self.sent_addrs = set()
        try:
            for line in open('spammer-email-sent').readlines():
                if not line: continue
                self.sent_addrs.add(line.strip())
            self.log.debug('loaded sent list')
        except:
            self.log.debug('sent list not found')

    def _parse_blacklist(self):
        '''Parse the blacklist of email.'''

        self.black_addrs = set()
        try:
            for line in open('spammer-email-blacklist').readlines():
                self.black_addrs.add(line.strip())
            self.log.debug('loaded blacklist')
        except:
            self.log.debug('blacklist not found')

    def _single_send(self, recipient, msg):
        try:
            if config.conf['spammer']['really']:
                self.mailer.send(msg)
            self.sent_addrs.add(recipient['email'])
            f = open('spammer-email-sent', 'a')
            f.write('%s\n' % recipient['email'])
            f.close()

        except spamalot.NoMoreAttemptsException, e:
            self.log.info('Too much errors for %s, will try later' %\
                recipient['email'])

        except smtplib.SMTPRecipientsRefused, e:
            self.log.warning('SMTP server refused the recipient: %s' % e)
            self.black_addrs.add(recipient['email'])
            f = open('spammer-email-blacklist', 'a')
            f.write('%s\n' % recipient['email'])
            f.close()

    def _send(self, to_addrs):
        delay = config.conf['spammer']['delay']

        for recipient in self.recipients:
            if recipient['email'] in to_addrs:
                msg = self._prepare_message(recipient)
                self._single_send(recipient, msg)
                time.sleep(delay)
            else:
                self.log.debug('skipping %s' % recipient['email'])

    def send(self):
        self.log.info('spamming started, found %d recipients' % len(self.left_addrs))

        attempt = 1
        tot_attemps = 3
        while attempt <= tot_attemps and self.left_addrs:
            self.log.debug('start attempt #%d' % attempt)
            self._send(self.left_addrs)
            attempt -= 1

        if not self.left_addrs:
            self.log.info("spamming finished, everything fine capt'n!")
        else:
            self.log.warning('there are %d left email to send!' % len(self.left_addrs))

if __name__ == '__main__':
    spamalot.init_mailer('spam.ini')
    mailer = spamalot.Mailer(batch=True)
    spammer = Spammer(mailer)
    spammer.send()

