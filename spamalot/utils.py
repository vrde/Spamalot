import csv

class UnicodeCSVDictReader(csv.DictReader):
    '''Convert each line to the specified encoding.'''

    def __init__(self, f, encoding='utf-8', sanitize=True, *args, **kw):
        '''Create a new reader.'''
        self.encoding = encoding
        self.sanitize = sanitize
        csv.DictReader.__init__(self, f, *args, **kw)

    def next(self):
        raw = csv.DictReader.next(self)
        clean = dict()

        for k, v in raw.items():
            clean_v = v.decode(self.encoding)
            if self.sanitize:
                clean_v = clean_v.strip()
            clean[k] = clean_v

        return clean

