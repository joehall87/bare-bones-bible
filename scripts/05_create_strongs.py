import json
import os
import os.path
import re
import sys
import unicodedata

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

from b3.greek import Greek
from b3.hebrew import Hebrew

GRE = Greek()
HEB = Hebrew()

# Assumes you have git cloned "strongs" repo in a dir called openscriptures
OS_STRONGS_DIR = os.path.join(os.path.dirname(ROOT_DIR), 'openscriptures', 'strongs')
MY_STRONGS_DIR = os.path.join(ROOT_DIR, 'resources', 'strongs')

_SEARCH_URL = '/search?text={id}&lan={lan}'
_BLB_URL = 'https://www.blueletterbible.org/lang/lexicon/lexicon.cfm?strongs={id}'
_BHUB_URL = 'https://biblehub.com/{lan}/{id}.htm'

_ID_RE = re.compile('[HG]\d+')


def run():
    """Parse openscriptures strongs js-files and make my own."""
    if not os.path.exists(MY_STRONGS_DIR):
        os.mkdir(MY_STRONGS_DIR)
    hebrew = {id_: _parse_entry(id_, entry, 'hebrew') for id_, entry in _load('hebrew').items()}
    greek = {id_: _parse_entry(id_, entry, 'greek') for id_, entry in _load('greek').items()}
    _write('hebrew', hebrew)
    _write('greek', greek)


def _parse_entry(id_, entry, lan):
    lemma = entry['lemma']
    if lan == 'greek':
        lemma = _strip_accents(entry['lemma'])
    helper = {'hebrew': HEB, 'greek': GRE}[lan]
    tlit = helper.transliterate(lemma)
    deriv = _ID_RE.sub('<a href="/search?text=\g<0>&lan={}">\g<0></a>'.format(lan), entry.get('derivation', ''))
    desc = (
        '<p>[<a href="{url}">{id}</a>] '
        '<strong>{lemma} {pron}</strong> - {deriv} {strongs_def}; {kjv_def} '
        '[<a href="{blb}" target="_blank">BLB</a>] '
        '[<a href="{bhub}" target="_blank">BibleHub</a>]</p>'
    ).format(
        id=id_, 
        url=_SEARCH_URL.format(id=id_, lan=lan),
        lemma=entry['lemma'], 
        pron=entry['pron' if lan == 'hebrew' else 'translit'],
        deriv=deriv,
        strongs_def=entry.get('strongs_def', ''), 
        kjv_def=entry.get('kjv_def', ''), 
        blb=_BLB_URL.format(id=id_),
        bhub=_BHUB_URL.format(id=id_[1:], lan=lan),
    )
    return {'id': id_, 'lemma': lemma, 'tlit': tlit, 'desc': desc}


def _load(lan):
    json_str = ''
    with open(os.path.join(OS_STRONGS_DIR, lan, 'strongs-' + lan + '-dictionary.js'), 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('var'):
                json_str = line.split('=', 1)[1].strip()
            elif line.startswith('"') or line.startswith('}'):
                json_str += '\n' + line.strip(';')
    return json.loads(json_str)


def _write(lan, obj):
    with open(os.path.join(MY_STRONGS_DIR, lan + '.json'), 'w') as f:
        json.dump(obj, f)


def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == '__main__':
    run()