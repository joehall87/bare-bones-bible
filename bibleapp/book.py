

class Book(object):
    def __init__(self, name):
        self.name = name
        self.code = name.replace(' ', '').lower()[:3]