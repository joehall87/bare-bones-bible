from collections import defaultdict
import json
import os.path
import re

import bs4
import requests

from bibleapp.book import Tanakh


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
OPENSCRIPTURES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources', 'openscriptures')


def run():
    """Create an easy-to-use json Hebrew lexicon."""
    print('1. Loading translations')
    translations = _load_translations()

    print('2. Loading lexical index')
    lexical_index = _load_lexical_index()

    print('3. Creating lexicon')
    lexicon = defaultdict(lambda: {
        'trans': None,
        'root': None,
        'refs': [],
        'index': None,
        'variants': set(),
    })
    tanakh = Tanakh()
    for book in tanakh.books:
        for c, verses in book.iter_verses_by_chapter():
            for verse in verses:
                for token in verse.he_tokens:
                    w = _clean(token.word)
                    root = _find_root(w, lexical_index)
                    lexicon[w]['trans'] = translations.get(w)
                    lexicon[w]['root'] = root
                    root = root or w
                    lexicon[root]['trans'] = translations.get(root)
                    lexicon[root]['refs'].append((book.code, c, verse.num))
                    lexicon[root]['index'] = lexical_index[root]
                    lexicon[root]['variants'].add(token.word)
    for entry in lexicon.values():
        if entry['root']:
            entry.pop('refs')
            entry.pop('index')
            entry.pop('variants')
        else:
            entry.pop('root')
            entry['variants'] = sorted(entry['variants'])

    print('4. Persist')
    with open(os.path.join(OPENSCRIPTURES_DIR, 'CustomHebrewLexicon.json'), 'w') as f:
        json.dump(lexicon, f)


def _find_root(w, lexical_index):
    # TODO: Do this nicer e.g. by considering actual prefix-chars
    if w not in lexical_index:
        for i, j in [(1, None), (None, -1), (1, -1), (None, -2), (1, -2)]:
            if w[i:j] in lexical_index:
                return w[i:j]


def _load_translations():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_lexical_index():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'LexicalIndex.xml'), 'r') as f:
        index_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    index = defaultdict(list)
    strongs = _load_strongs()
    for x in index_xml.find_all('entry'):
        w = _get(x, 'w')
        entry = {
            'w': w,
            'pos': _get(x, 'pos'),
            'def': _get(x, 'def'),
            'strongs': {},
        }
        xref = x.find('xref')
        if xref and 'strong' in xref.attrs and xref['strong'].isdigit():
            entry['strongs'] = strongs[xref['strong']]
        index[_clean(w)].append(entry)
    for w in index:
        index[w] = sorted(index[w], key=lambda x: x['strongs'].get('id', ''))
    return index


def _load_strongs():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    return {x['id'][1:]: {  # Strip out the H
        'id': x['id'],
        'pron': x.find('w')['pron'],
        'desc': '{}; {}'.format(_get(x, 'meaning'), _get(x, 'usage')).replace('None; ', '').replace('; None', ''),
        #'xlit': x.find('w')['xlit'],
        #'source': _get(x, 'source'),
    } for x in strongs_xml.find_all('entry')}


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


def _clean(w):
    return re.sub('[^\u05D0-\u05EA]', '', w)


if __name__ == "__main__":
    run()
    