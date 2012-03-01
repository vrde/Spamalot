# -*- coding: utf-8 -*-

from spamalot.utils import UnicodeCSVDictReader
import StringIO

def test_encoding():
    sf = StringIO.StringIO()
    sf.write('id,name,email\n')
    sf.write('1,föö,Mr. Foo Bar <foo@bar.com>\n')
    sf.write('2,yay,  Sanitize me <yay@sanitize.me>      \n')
    sf.write('3,Silvio, banana@republic.it\n')
    sf.seek(0, 0)

    ud = UnicodeCSVDictReader(sf)
    row = ud.next()
    assert row == {
        'id': '1',
        'name': u'föö',
        'email': 'Mr. Foo Bar <foo@bar.com>'}

    row = ud.next()
    assert row == {
        'id': '2',
        'name': u'yay',
        'email': 'Sanitize me <yay@sanitize.me>'}

    row = ud.next()
    assert row == {
        'id': '3',
        'name': u'Silvio',
        'email': 'banana@republic.it'}

