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
    tanakh = Tanakh()
    heb = Hebrew()

    print('1. Loading translations')
    translations = _load_translations()

    print('2. Loading strongs')
    strongs = _load_strongs(heb)
    word_to_sid = _load_word_to_strongs_id(heb)
    # TODO: Possibly using the strongs-id as the "root" might be better...
    root_to_sids = defaultdict(set)
    for id_, entry in strongs.items():
        root_to_sids[entry['w-clean']].add(id_)
    root_to_sids = {root: sorted(ids, key=lambda x: int(x.strip('H'))) for root, ids in root_to_sids.items()}

    print('3. Creating lexicon')
    lexicon = {}
    lexicon_root = {}
    for book in tanakh.books:
        for verse in book.iter_verses():
            for i, token in enumerate(verse.he_tokens):
                ref = book.ref, verse.c, verse.v, i
                w = heb.strip_cantillations(token.word)
                if w not in lexicon:
                    trans = translations.get(_clean(w))
                    sid = word_to_sid.get(heb.sort_niqqud(w))
                    entry = strongs.get(sid)
                    root = entry['w-clean'] if entry else w
                    root_trans = translations.get(root)
                    lexicon[w] = {
                        'trans': trans,
                        'root': root,
                        'root-trans': root_trans,
                        'sid': sid,
                        'refs': [],
                    }
                lexicon[w]['refs'].append(ref)
                root = lexicon[w]['root']
                if root:
                    if root not in lexicon_root:
                        lexicon_root[root] = {
                            'sids': root_to_sids.get(root, []),
                            'refs': [],
                        }
                    lexicon_root[root]['refs'].append(ref)

    print('4. Persist')
    with open(os.path.join(LEXICON_DIR, 'Strongs.json'), 'w') as f:
        json.dump(strongs, f)
    with open(os.path.join(LEXICON_DIR, 'Lexicon.json'), 'w') as f:
        json.dump(lexicon, f)
    with open(os.path.join(LEXICON_DIR, 'LexiconRoot.json'), 'w') as f:
        json.dump(lexicon_root, f)


def _load_translations():
    with open(os.path.join(LEXICON_DIR, 'GoogleTranslations.json'), 'r') as f:
        return json.load(f)


def _load_strongs(heb):
    with open(os.path.join(LEXICON_DIR, 'HebrewStrong.xml'), 'r') as f:
        strongs_xml = bs4.BeautifulSoup(f.read(), 'html.parser')
    strongs = {}
    for x in strongs_xml.find_all('entry'):
        w = heb.strip_cantillations(_get(x, 'w'))
        strongs[x['id']] = {
            'id': x['id'],
            'w': w,
            'w-clean': _clean(w),
            'pron': x.find('w')['pron'],
            'desc': '{}; {}'.format(_get(x, 'meaning'), _get(x, 'usage')).replace('None; ', '').replace('; None', ''),
        }
    return strongs


def _load_word_to_strongs_id(heb):
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
                    w2 = w.replace('\u05b9\u05d5', '\u05d5\u05b9')
                    sid = 'H' + sid.group(1).strip('abcd')  # <- HebrewStrong.xml doesn't seem to support
                    strongs_map[w][sid] += 1                #    these "sub-entries"
                    if w != w2:
                        strongs_map[w2][sid] += 1
    strongs_map = {w: sorted(counts.items(), key=lambda x: x[1])[-1][0] for w, counts in strongs_map.items()}
    return strongs_map


def _get(entry, child):
    if entry.find(child):
        return ''.join([str(x) for x in entry.find(child).contents])


def _clean(w):
    return re.sub('[^\u05D0-\u05EA]', '', w)


if __name__ == "__main__":
    run()
    
