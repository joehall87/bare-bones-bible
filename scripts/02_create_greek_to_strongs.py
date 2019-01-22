import glob
import json
import os
import os.path
import re
import requests
import sys
import unicodedata


ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
VERSE_RE = re.compile('<a href="/greek/(\d+)\.htm"[^>]+>([^a-z<]+)</a>')
MY_STRONGS_DIR = os.path.join(ROOT_DIR, 'resources', 'strongs')
BHUB_URL = 'https://biblehub.com/psb/{b}/{c}.htm'


BHUB_BOOK_IDS = [
    'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1_Corinthians', '2_Corinthians',
    'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1_Thessalonians', '2_Thessalonians',
    '1_Timothy', '2_Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1_Peter', '2_Peter',
    '1_John', '2_John', '3_John', 'Jude', 'Revelation',
]


def run():
    """Scrape bible-hub to get a mapping from greek word -> strongs-id."""
    if not os.path.exists(MY_STRONGS_DIR):
        os.mkdir(MY_STRONGS_DIR)
    greek_to_strongs = {}
    for bhub_id in BHUB_BOOK_IDS:
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
            greek_to_strongs.update({
                _strip_accents(match.group(2).strip()).lower(): 'G' + match.group(1) 
                for match in VERSE_RE.finditer(content)
            })
    with open(os.path.join(MY_STRONGS_DIR, 'greek-to-strongs.json'), 'w') as f:
        json.dump(greek_to_strongs, f)


def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == '__main__':
    run()
