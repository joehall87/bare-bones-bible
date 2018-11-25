from collections import defaultdict
import logging
import os

# Have to install Translator in a dodgy way due to following issue:
# https://stackoverflow.com/questions/52455774/googletrans-stopped-working-with-error-nonetype-object-has-no-attribute-group
from googletrans import Translator
import untangle


logging.basicConfig(format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO)


STRONGS_FILE = os.path.join(os.environ['HOME'], 'src', 'openscriptures', 'strongs', 'hebrew', 'StrongHebrewG.xml')


class Hebrew(object):
    def __init__(self):
        self._gtrans = Translator()
        self._strongs = defaultdict(lambda: {'ids': [], 'explanations': [], 'translations': []})
        xml = untangle.parse(STRONGS_FILE)
        for entry in xml.osis.osisText.div.div:
            word = entry.w.cdata.strip()
            expln = [x for x in entry.note if x['type'] == 'explanation'][0].cdata
            trans = [x for x in entry.note if x['type'] == 'translation'][0].cdata
            self._strongs[word]['ids'].append(entry.w['ID'])
            self._strongs[word]['explanations'].append(expln)
            self._strongs[word]['translations'].append(trans)

    def to_hebrew(self, word):
        """Translate to hebrew using Google-translate"""
        return self._gtrans.translate(word, dest='he').text

    def to_english(self, word):
        """Translate to english using Google-translate"""
        return self._gtrans.translate(word, dest='en').text

    def strongs(self, word):
        """Get the strong's entry for this word"""
        return self._strongs[word]

    def show(self, word):
        """Pretty print the entry for the word"""
        en = self.to_english(word)
        entry = self.strongs(word)
        print("***** {} *****".format(word))
        print('Meaning: "{}"'.format(en))
        for id, exp, trans in zip(entry['ids'], entry['explanations'], entry['translations']):
            print(id)
            print('-', exp)
            print('-', trans)
