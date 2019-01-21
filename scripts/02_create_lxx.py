import glob
import json
import os
import os.path
import re
import requests
import sys
import unicodedata

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

from b3.greek import Greek

GREEK = Greek()
MY_LXX_DIR = os.path.join(ROOT_DIR, 'resources', 'lxx')

# Assumes you have git cloned "GreekResources" repo in a dir called openscriptures
WORD_LOOKUP_PATH = os.path.join(os.path.dirname(ROOT_DIR), 'openscriptures', 'GreekResources', 'GreekWordList.js')

BHUB_BOOK_IDS = [
    'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges', 
    '1_Samuel', '2_Samuel', '1_Kings', '2_Kings', 'Isaiah', 'Jeremiah', 
    'Ezekiel', 'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 
    'Habakkuk', 'Zephaniah', 'Haggai', 'Zechariah', 'Malachi', 'Psalms', 'Proverbs', 
    'Job', 'Songs', 'Ruth', 'Lamentations', 'Ecclesiastes', 'Esther', 'Daniel', 
    'Ezra', 'Nehemiah', '1_Chronicles', '2_Chronicles',
]
MY_BOOK_IDS = [
    'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', '1Sa', '2Sa', '1Ki', '2Ki', 
    'Isa', 'Jer', 'Eze', 'Hos', 'Joe', 'Amo', 'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal',
    'Psa', 'Pro', 'Job', 'Sng', 'Rth', 'Lam', 'Ecc', 'Est', 'Dan', 'Ezr', 'Neh', '1Ch', '2Ch',
]

BHUB_URL = 'https://biblehub.com/sepd/{b}/{c}.htm'
VERSE_RE = re.compile('<span [^>]+reftext[^>]+><a [^>]+><b>\d+</b></a></span>([^<]+)')


def run():
    """Scrape bible-hub to get LXX greek text with KJV versification."""
    _check_dirs()
    _create_lxx()


def _create_lxx():
    _check_dirs()
    id_map = dict(zip(BHUB_BOOK_IDS, MY_BOOK_IDS))
    word_lookup = _load_word_lookup()
    for bhub_id in BHUB_BOOK_IDS:
        path = os.path.join(MY_LXX_DIR, id_map[bhub_id] + '.json')
        text = _load_text(bhub_id)
        text = [[_clean_verse(v, word_lookup) for v in c] for c in text]
        with open(path, 'w') as f:
            json.dump({'text': text}, f)


def _check_dirs():
    if not os.path.exists(MY_LXX_DIR):
        os.mkdir(MY_LXX_DIR)
    if not os.path.exists(os.path.join(MY_LXX_DIR, '_cache')):
        os.mkdir(os.path.join(MY_LXX_DIR, '_cache'))


def _load_text(bhub_id):
    cache_path = os.path.join(MY_LXX_DIR, '_cache', bhub_id + '.json')
    if os.path.exists(cache_path):
        print('Loading cached {}'.format(bhub_id))
        with open(cache_path, 'r') as f:
            return json.load(f)['text']
    else:
        text = []
        for c in range(1, 200):
            print('Scraping {} {}'.format(bhub_id, c))
            url = BHUB_URL.format(b=bhub_id.lower(), c=c)
            resp = requests.get(url)
            if resp.status_code == 404:
                if c > 1:
                    break
                else:
                    raise ValueError('Hmm, this seems broken: {}'.format(url))
            content = resp.content.decode('utf-8')
            chapter = [match.group(1).strip() for match in VERSE_RE.finditer(content)]
            text.append(chapter)
        with open(cache_path, 'w') as f:
            json.dump({'text': text}, f)
        return text


def _clean_verse(verse, word_lookup):
    verse = verse.replace('\xb7', '')                # Ignore the random center-dots
    verse = verse.replace('[', '').replace(']', '')  # Ignore the brackets for now
    verse = verse.replace('.', '').replace(',', '')  # ...and punctuation
    verse = verse.lower()
    tokens = ((w, _strip_accents(w)) for w in verse.split())
    tokens = ((w, ws, GREEK.transliterate(ws)) for w, ws in tokens)
    tokens = ((w, ws, tlit, word_lookup.get(ws, {}).get('strong', '')) for w, ws, tlit in tokens)
    return [(w, ws, tlit, ('G' if strong else '') + strong) for w, ws, tlit, strong in tokens]


def _load_word_lookup():
    json_str = ''
    with open(WORD_LOOKUP_PATH, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('"'):
                json_str += line
    return json.loads('{' + json_str + '}')


def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == '__main__':
    run()
