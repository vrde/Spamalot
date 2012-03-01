#!/usr/bin/env python

from setuptools import setup

setup(
    name='Spamalot',
    version='0.0.4',
    description='Python simple mailer',
    author='Alberto Granzotto (vrde)',
    author_email='vrde@tastybra.in',
    url='https://github.com/vrde/Spamalot',

    packages=['spamalot'],

    package_data = {
        'spamalot': ['conf/*']
    },

    install_requires=[
        'ConfigObj',
        'setuptools'
    ]
)

