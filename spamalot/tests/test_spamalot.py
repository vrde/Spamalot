# -*- coding: utf-8 -*-

import smtplib
import re

from spamalot import Message, NoMoreAttemptsException

def test_sender_send(mailer, force_reply, server):
    mailer.send(Message('foo@bar.com', 'foobar', 'asd'))
    assert 'From: Test <test@localhost>' in server.last_data
    assert re.search('^Subject:.*foobar', server.last_data, re.MULTILINE)

def test_iso_8859_15_subject_send(mailer, force_reply, server):
    mailer.send(Message('foo@bar.com', u'fööbär', 'asd'))
    assert 'Subject: =?iso-8859-15?q?f=F6=F6b=E4r?=' in server.last_data

def test_utf_8_subject_send(mailer, force_reply, server):
    mailer.send(Message('foo@bar.com', u'fööbär', 'asd', encoding='utf-8'))
    assert 'Subject: =?utf-8?b?ZsO2w7Ziw6Ry?=' in server.last_data

def test_iso_8859_15_body_send(mailer, force_reply, server):
    mailer.send(Message('foo@bar.com', 'foobar', u'über cüte lòl cåt'))
    assert '=FCber c=FCte l=F2l c=E5t' in server.last_data

def test_utf_8_body_send(mailer, force_reply, server):
    mailer.send(Message('foo@bar.com', 'foobar', u'über cüte lòl cåt', encoding='utf-8'))
    assert u'über cüte lòl cåt'.encode('utf-8') in server.last_data

def test_no_more_attempts(mailer, server):
    return
    #server.stop()
    try:
        mailer.send(Message('foo@bar.com', 'foobar', 'asd'))
        assert False
    except NoMoreAttemptsException:
        pass

def test_sender_refused(mailer, force_reply):
    force_reply('MAIL', '500')
    try:
        mailer.send(Message('foo@bar.com', 'foobar', 'asd'))
        assert False
    except smtplib.SMTPSenderRefused:
        pass

def test_recipients_refused(mailer, force_reply):
    force_reply('RCPT', '500')
    try:
        mailer.send(Message('foo@bar.com', 'foobar', 'asd'))
        assert False
    except smtplib.SMTPRecipientsRefused:
        pass

def test_data_error(mailer, force_reply):
    force_reply('DATA', '500')
    try:
        mailer.send(Message('foo@bar.com', 'foobar', 'asd'))
        assert False
    except smtplib.SMTPDataError:
        pass

