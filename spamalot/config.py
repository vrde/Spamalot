from configobj import ConfigObj, flatten_errors
from validate import Validator

import logging
import logging.config

import pkg_resources

conf = None
log = None

# sorry about that...
class Dummy(object):
    def foo(self, *args, **kw):
        pass
    def __getattr__(self, name):
        return self.foo

def _trim_config(configuration, prefix):
    # ty SQLAlchemy :P
    options = dict((key[len(prefix):], configuration[key])
                   for key in configuration
                   if key.startswith(prefix))
    return options

def init_from_config(configuration, prefix='spamalot.'):
    mailer = _trim_config(configuration, '%s%s' % (prefix, 'mailer.'))
    logger = _trim_config(configuration, '%s%s' % (prefix, 'logger.'))
    options = {'mailer': mailer, 'logger': logger}
    init_mailer(options)

def init_mailer(configfile=None):
    """Feed the mailer with the configuration file"""
    
    global conf, log

    configspec = pkg_resources.resource_filename('spamalot',
        'conf/configspec.ini')
    logconfig = pkg_resources.resource_filename('spamalot',
        'conf/logging.ini')
    
    conf = ConfigObj(configfile, configspec=configspec)
    validator = Validator()
    results = conf.validate(validator)

    if results != True:
        for (section_list, key, _) in flatten_errors(conf, results):
            if key is not None:
                print 'The "%s" key in the section "%s" failed validation' %\
                    (key, ', '.join(section_list))
            else:
                print 'The following section was missing' % ', '.join(section_list)
        exit(0)

    if conf['logging']['outfile']:
        defaults = {
            'custom_outfile': conf['logging']['outfile'],
            'custom_mode': conf['logging']['mode'],
            'custom_level': conf['logging']['level']
        }

        logging.config.fileConfig(logconfig, defaults)
#    else:
#        log = Dummy()
    log = logging.getLogger('spamalot')
    log.info('spamalot initialised')

