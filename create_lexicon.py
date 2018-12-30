from collections import defaultdict
import json
import os.path
import re

import bs4
import requests

from bibleapp.book import Tanakh


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
LEXICON_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', 'lexicon')


PREFIXES = ['and', 'as', 'at', 'for', 'from', 'in', 'like', 'on', 'the', 'to', 'when', 'will', 'with', 'you will']
SUFFIXES = ['he', 'her', 'his', 'my', 'our', 'she', 'their', 'they', 'we', 'you', 'your']
PRE_AND_SUF = ['as they', 'in her', 'in his', 'in my', 'in their', 'they will', 'to her', 'to his', 'to my', 'to our', 'to their', 'with her', 'with his']


def run():
    """Create an easy-to-use json Hebrew lexicon."""
    print('1. Loading translations')
    translations = _load_translations()

    print('2. Loading strongs')
    strongs = _load_strongs()

    print('3. Creating lexicon')
    lexicon = defaultdict(lambda: {
        'trans': None,
        'root': None,
        'refs': [],
        'strongs': [],
        'variants': set(),
    })
    tanakh = Tanakh()
    for book in tanakh.books:
        for c, verses in book.iter_verses_by_chapter():
            for verse in verses:
                for token in verse.he_tokens:
                    w = _clean(token.word)
                    root = _find_root(w, translations)
                    lexicon[w]['trans'] = translations.get(w)
                    lexicon[w]['root'] = root
                    root = root or w
                    lexicon[root]['trans'] = translations.get(root)
                    lexicon[root]['refs'].append((book.code, c, verse.num))
                    lexicon[root]['strongs'] = strongs[root]
                    lexicon[root]['variants'].add(w)
    for entry in lexicon.values():
        entry['variants'] = sorted(entry['variants'])

    print('4. Persist')
    with open(os.path.join(LEXICON_DIR, 'CustomHebrewLexicon.json'), 'w') as f:
        json.dump(lexicon, f)


def _find_root(w, translations):
    en = translations[w]
    if en:
        en = {  # Couple of horrible hacks
            'Genesis': 'the genesis',
            'Country': 'the country',
        }.get(en, en).lower()
        if any(en.startswith(prefix + ' ') for prefix in ['and the']):
            return w[2:]
        if any(en.startswith(prefix + ' ') for prefix in ['and', 'the']):
            return w[1:]


def _load_translations():
    with open(os.path.join(LEXICON_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_strongs():
    with open(os.path.join(LEXICON_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    strongs = defaultdict(list)
    for x in strongs_xml.find_all('entry'):
        w = _get(x, 'w')
        strongs[_clean(w)].append({
            'id': x['id'],
            'w': _get(x, 'w'),
            'pron': x.find('w')['pron'],
            'desc': '{}; {}'.format(_get(x, 'meaning'), _get(x, 'usage')).replace('None; ', '').replace('; None', ''),
            #'xlit': x.find('w')['xlit'],
            #'source': _get(x, 'source'),
        })
    for key in strongs:
        strongs[key] = sorted(strongs[key], key=lambda x: x['id'])
    return strongs


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


def _clean(w):
    return re.sub('[^\u05D0-\u05EA]', '', w)


if __name__ == "__main__":
    run()
    