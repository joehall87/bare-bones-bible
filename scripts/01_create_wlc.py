import json
import os
import os.path
import re
import sys
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

from b3.hebrew import Hebrew

HEB = Hebrew()

# Assumes you have git cloned morphhb repo in a dir called openscriptures
OS_WLC_DIR = os.path.join(os.path.dirname(ROOT_DIR), 'openscriptures', 'morphhb', 'wlc')
MY_WLC_DIR = os.path.join(ROOT_DIR, 'resources', 'wlc')

OS_BOOK_IDS = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', '1Sam', '2Sam', '1Kgs', '2Kgs', 
    'Isa', 'Jer', 'Ezek', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Ps', 'Prov', 'Job', 'Song', 'Ruth', 'Lam', 'Eccl', 'Esth', 'Dan', 'Ezra', 'Neh', '1Chr', '2Chr',
]
MY_BOOK_IDS = [
    'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', '1Sa', '2Sa', '1Ki', '2Ki', 
    'Isa', 'Jer', 'Eze', 'Hos', 'Joe', 'Amo', 'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal',
    'Psa', 'Pro', 'Job', 'Sng', 'Rth', 'Lam', 'Ecc', 'Est', 'Dan', 'Ezr', 'Neh', '1Ch', '2Ch',
]


def run():
    """Parse openscriptures xml-files and make my own json ones."""
    if not os.path.exists(MY_WLC_DIR):
        os.mkdir(MY_WLC_DIR)
    for os_book_id, my_book_id in zip(OS_BOOK_IDS, MY_BOOK_IDS):
        path = os.path.join(MY_WLC_DIR, '{}.json'.format(my_book_id))
        print('Creating {}'.format(path))
        tree = _parse_xml(os_book_id)
        text = list(_make_text(tree))
        with open(path, 'w') as f:
            json.dump({'text': text}, f)


def _parse_xml(name):
    with open(os.path.join(OS_WLC_DIR, '{}.xml'.format(name)), 'r') as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
    return ET.fromstring(xmlstring)


def _make_text(tree):
    prev_cv = 1, 1
    chapter, verse_tokens = [], []
    for verse in tree.findall('*/div/chapter/verse'):
        cv = _ref_to_cv(verse.attrib['osisID'])
        for elem in verse.findall('*'):
            if elem.tag == 'note' and (elem.text or '').startswith('KJV:'):
                cv = _ref_to_cv(elem.text[4:].strip('!abcd'))
            elif elem.tag == 'w':
                if cv > prev_cv and verse_tokens:
                    chapter.append(_clean(verse_tokens))
                    verse_tokens = []
                    if cv[0] > prev_cv[0]:
                        yield chapter
                        chapter = []
                    prev_cv = cv
                verse_tokens.append(_parse_w_elem(elem))
            elif elem.tag == 'seg':
                seg = {
                    'x-maqqef': '\u05BE',
                    'x-paseq': ' \u05C0 ',
                    'x-pe': ' (\u05E4) ',
                    'x-reversednun': ' (\u05C6) ',  # <- Appears in some Psalms
                    'x-samekh': ' (\u05E1) ',
                    'x-sof-pasuq': '\u05C3 ',
                }[elem.attrib['type']]
                verse_tokens[-1][-2] += seg
                verse_tokens[-1][-1] = HEB.transliterate(verse_tokens[-1][-2])
    chapter.append(_clean(verse_tokens))
    yield chapter


def _ref_to_cv(ref):
    c, v = ref.split('.')[1:]
    return int(c), int(v)


def _parse_w_elem(elem):
    w = HEB.strip_cantillations(elem.text.replace('/',''))
    ws = HEB.strip_niqqud(w)
    tw = HEB.transliterate(w)
    strongs = re.sub('\D', '', elem.attrib['lemma']) or None
    if strongs:
        strongs = 'H' + strongs
    return [w, ws, tw, strongs, '', '']


def _clean(tokens):
    return [(w, ws, tw, strongs, seg or ' ', tseg or ' ') 
            for w, ws, tw, strongs, seg, tseg in tokens]


if __name__ == '__main__':
    run()