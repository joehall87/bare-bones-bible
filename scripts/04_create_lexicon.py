from collections import Counter, defaultdict
import glob
import json
import os.path
import re

import bs4
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from bibleapp.book import Tanakh
from bibleapp.hebrew import Hebrew


# Need to put HebrewStrong.xml and LexicalIndex.xml from https://github.com/openscriptures/HebrewLexicon into this dir:
LEXICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'lexicon')


PREFIXES = ['and', 'as', 'at', 'for', 'from', 'in', 'like', 'on', 'the', 'to', 'when', 'will', 'with', 'you will']
SUFFIXES = ['he', 'her', 'his', 'my', 'our', 'she', 'their', 'they', 'we', 'you', 'your']
PRE_AND_SUF = ['as they', 'in her', 'in his', 'in my', 'in their', 'they will', 'to her', 'to his', 'to my', 'to our', 'to their', 'with her', 'with his']


def run():
    """Create an easy-to-use json Hebrew lexicon."""
    heb = Hebrew()

    print('1. Loading translations')
    translations = _load_translations()

    print('2. Loading strongs')
    entries = _load_strongs_entries(heb)
    strongs = _load_word_to_strongs(heb)
    strongs = {word: entries[id_] for word, id_ in strongs.items() if id_ in entries}
    variants = defaultdict(set)
    #variants = {i: sorted(ws) for i, ws in variants.items()}

    print('3. Creating lexicon')
    lexicon = {}
    references = defaultdict(list)
    tanakh = Tanakh()
    for book in tanakh.books:
        for verse in book.iter_verses():
            ref = book.ref, verse.c, verse.v
            for token in verse.he_tokens:
                w = heb.strip_cantillations(token.word)
                references[w].append(ref)
                if w not in lexicon:
                    w2 = heb.sort_niqqud(w)
                    entry = strongs.get(w2)
                    if not entry:
                        entry = strongs.get(w2.replace('\u05d5\u05b9', '\u05b9\u05d5'))
                    root = entry['w'] if entry else w
                    #vars_ = sorted(set(v for entry in entries for v in variants[entry['id']] if v != w))
                    lexicon[w] = {
                        'trans': translations.get(_clean(w)),
                        'root': root,
                        'strongs': entry,
                        #'variants': vars_,
                    }

    print('4. Persist')
    with open(os.path.join(LEXICON_DIR, 'Lexicon.json'), 'w') as f:
        json.dump(lexicon, f)
    with open(os.path.join(LEXICON_DIR, 'References.json'), 'w') as f:
        json.dump(references, f)


def _load_translations():
    with open(os.path.join(LEXICON_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_strongs_entries(heb):
    with open(os.path.join(LEXICON_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    strongs = {}
    for x in strongs_xml.find_all('entry'):
        strongs[x['id']] = {
            'id': x['id'],
            'w': heb.strip_cantillations(_get(x, 'w')),
            'pron': x.find('w')['pron'],
            'desc': '{}; {}'.format(_get(x, 'meaning'), _get(x, 'usage')).replace('None; ', '').replace('; None', ''),
            #'xlit': x.find('w')['xlit'],
            #'source': _get(x, 'source'),
        }
    return strongs


def _load_word_to_strongs(heb):
    # Figure out a unique mapping from word -> strongs-id based on bible-hub scrapings
    strongs_map = defaultdict(lambda: Counter())
    for path in glob.glob(os.path.join(LEXICON_DIR, 'BibleHubScrape.*.json')):
        with open(path, 'r') as f:
            data = json.load(f)['data']
        for item in data:
            for row in re.findall('<tr>.*?</tr>', item['html'])[1:]:
                w = heb.strip_cantillations(re.search('<span="hebrew3">([^<]*)</span>', row).group(1))
                w = heb.strip_punctuation(w)
                w = heb.sort_niqqud(w)
                sid = re.search('http://strongsnumbers.com/hebrew\/(\w+)\.htm', row)
                if w and sid:
                    sid = 'H' + sid.group(1).strip('abcd')  # <- HebrewStrong.xml doesn't seem to support
                    strongs_map[w][sid] += 1                #    these "sub-entries"
    strongs_map = {w: sorted(counts.items(), key=lambda x: x[1])[-1][0] for w, counts in strongs_map.items()}
    return strongs_map


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


def _clean(w):
    return re.sub('[^\u05D0-\u05EA]', '', w)


if __name__ == "__main__":
    run()
    
