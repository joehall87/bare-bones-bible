from collections import defaultdict
import glob
import json
import os.path
import re

import bs4
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from bibleapp.book import Tanakh


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
LEXICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'lexicon')


PREFIXES = ['and', 'as', 'at', 'for', 'from', 'in', 'like', 'on', 'the', 'to', 'when', 'will', 'with', 'you will']
SUFFIXES = ['he', 'her', 'his', 'my', 'our', 'she', 'their', 'they', 'we', 'you', 'your']
PRE_AND_SUF = ['as they', 'in her', 'in his', 'in my', 'in their', 'they will', 'to her', 'to his', 'to my', 'to our', 'to their', 'with her', 'with his']


def run():
    """Create an easy-to-use json Hebrew lexicon."""
    print('1. Loading translations')
    translations = _load_translations()

    print('2. Loading strongs')
    entries = _load_strongs_entries()
    strongs = _load_word_to_strongs()
    variants = defaultdict(set)
    for word, ids in strongs.items():
        strongs[word] = [entries[id_] for id_ in ids if id_ in entries]
        for id_ in ids:
            variants[id_].add(word)
    variants = {i: sorted(ws) for i, ws in variants.items()}

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
        for verse in book.iter_verses():
            ref = book.ref, verse.c, verse.v
            for token in verse.he_tokens:
                w = _clean(token.word)
                if w not in lexicon:
                    entries = strongs.get(w, [])
                    root = _clean(entries[0]['w']) if entries else w
                    vars_ = sorted(set(v for entry in entries for v in variants[entry['id']] if v != w))
                    lexicon[w] = {
                        'trans': translations.get(w),
                        'root': root,
                        'refs': [ref],
                        'strongs': entries,
                        'variants': vars_,
                    }
                else:
                    lexicon[w]['refs'].append(ref)

    print('4. Persist')
    with open(os.path.join(LEXICON_DIR, 'CustomHebrewLexicon.json'), 'w') as f:
        json.dump(lexicon, f)


def _load_translations():
    with open(os.path.join(LEXICON_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_strongs_entries():
    with open(os.path.join(LEXICON_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    strongs = {}
    for x in strongs_xml.find_all('entry'):
        strongs[x['id']] = {
            'id': x['id'],
            'w': _get(x, 'w'),
            'pron': x.find('w')['pron'],
            'desc': '{}; {}'.format(_get(x, 'meaning'), _get(x, 'usage')).replace('None; ', '').replace('; None', ''),
            #'xlit': x.find('w')['xlit'],
            #'source': _get(x, 'source'),
        }
    return strongs


def _load_word_to_strongs():
    strongs_map = defaultdict(set)
    for path in glob.glob(os.path.join(LEXICON_DIR, 'BibleHubScrape.*.json')):
        with open(path, 'r') as f:
            data = json.load(f)['data']
        for item in data:
            for row in re.findall('<tr>.*?</tr>', item['html'])[1:]:
                heb = _clean(re.search('<span="hebrew3">([^<]*)</span>', row).group(1))
                if heb:
                    strongs_id = re.search('http://strongsnumbers.com/hebrew\/(\w+)\.htm', row).group(1)
                    strongs_id = 'H' + strongs_id.strip('abcd')  # <- Above strongs version doesn't seem to support
                    strongs_map[heb].add(strongs_id)             #    these "sub-entries"
    func = lambda x: (int(x.strip('Habcd')), x[-1])
    strongs_map = {heb: sorted(ids, key=func) for heb, ids in strongs_map.items()}
    return strongs_map


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


def _clean(w):
    return re.sub('[^\u05D0-\u05EA]', '', w)


if __name__ == "__main__":
    run()
    
