import json
import os.path

import bs4


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
OPENSCRIPTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'openscriptures')


def run():
    """Create an easy-to-use json Hebrew lexicon."""

    # 1. Parse Lexical Index
    with open(os.path.join(OPENSCRIPTURES_DIR, 'LexicalIndex.xml'), 'r') as f:
        lexicon = bs4.BeautifulSoup(f.read(), 'html.parser')
    lexicon = ({
        'w': _get(x, 'w'),
        'pos': _get(x, 'pos'),
        'def': _get(x, 'def'),
        'xref': x.find('xref'),
    } for x in lexicon.find_all('entry'))
    lexicon = {x['w']: {
        'w': x['w'],
        'pos': x['pos'],
        'def': x['def'],
        'strong': ('H' + x['xref']['strong']) if x['xref'] and 'strong' in x['xref'].attrs else None,
    } for x in lexicon}

    # 2. Parse Strongs
    with open(os.path.join(OPENSCRIPTURES_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs = bs4.BeautifulSoup(f.read(), 'html.parser')
    strongs = {x['id']: {
        'id': x['id'],
        'pron': x.find('w')['pron'],
        'xlit': x.find('w')['xlit'],
        'source': _get(x, 'source'),
        'meaning': _get(x, 'meaning'),
        'usage': _get(x, 'usage'),
    } for x in strongs.find_all('entry')}

    # 3. Join them
    for x in lexicon.values():
        x['strong'] = strongs.get(x['strong'], {})
    with open(os.path.join(OPENSCRIPTURES_DIR, 'CustomHebrewLexicon.json'), 'w') as f:
        json.dump(lexicon, f)


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


if __name__ == "__main__":
    run()
    