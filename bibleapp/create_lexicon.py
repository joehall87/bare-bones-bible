from collections import defaultdict
import json
import os.path
import re

import bs4
import requests

from book import Tanakh


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
OPENSCRIPTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'openscriptures')


def run():
    """Create an easy-to-use json Hebrew lexicon."""
    lexicon = _init_lexicon()
    translations = _load_translations()
    lexical_index = _load_lexical_index()
    strongs = _load_strongs()

    for w, entry in lexicon.items():
        strongs_id = lexical_index.get(w, {}).get('strong')
        entry['trans'] = translations.get(entry['w-clean'])
        entry['index'] = lexical_index.get(w, {})
        entry['strongs'] = strongs.get(strongs_id, {})

    with open(os.path.join(OPENSCRIPTURES_DIR, 'CustomHebrewLexicon.json'), 'w') as f:
        json.dump(lexicon, f)


def _init_lexicon():
    tanakh = Tanakh()
    occurrences = defaultdict(list)
    for book in tanakh.books:
        for c, verses in book.iter_verses_by_chapter():
            for verse in verses:
                for token in verse.he_tokens:
                    occurrences[token.word].append((book.code, c, verse.num))
    return {w: {
        'w': w, 
        'w-clean': re.sub('[^\u05D0-\u05EA]', '', w),
        'refs': refs,
    } for w, refs in occurrences.items()}


def _load_translations():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_lexical_index():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'LexicalIndex.xml'), 'r') as f:
        index = bs4.BeautifulSoup(f.read(), 'html.parser')
    index = ({
        'w': _get(x, 'w'),
        'pos': _get(x, 'pos'),
        'def': _get(x, 'def'),
        'xref': x.find('xref'),
    } for x in index.find_all('entry'))
    return {x['w']: {
        'pos': x['pos'],
        'def': x['def'],
        'strong': ('H' + x['xref']['strong']) if x['xref'] and 'strong' in x['xref'].attrs else None,
    } for x in index}


def _load_strongs():
    with open(os.path.join(OPENSCRIPTURES_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs = bs4.BeautifulSoup(f.read(), 'html.parser')
    return {x['id']: {
        'id': x['id'],
        'pron': x.find('w')['pron'],
        'xlit': x.find('w')['xlit'],
        'source': _get(x, 'source'),
        'meaning': _get(x, 'meaning'),
        'usage': _get(x, 'usage'),
    } for x in strongs.find_all('entry')}


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


if __name__ == "__main__":
    run()
    