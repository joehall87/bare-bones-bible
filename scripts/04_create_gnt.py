import json
import os
import os.path
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

from b3.greek import Greek


WORD_LOOKUP_PATH = os.path.join(ROOT_DIR, 'resources', 'strongs', 'greek-to-strongs.json')


def _load_word_lookup():
    with open(WORD_LOOKUP_PATH, 'r') as f:
        return json.load(f)


GREEK = Greek()
LOOKUP = _load_word_lookup()

# Assumes you have downloaded sblgnt.osis.zip from http://sblgnt.com/download/
# and extracted the .xml file into resources/gnt/_cache
GNT_DIR = os.path.join(ROOT_DIR, 'resources', 'gnt')

OS_BOOK_IDS = [
    'Matt', 'Mark', 'Luke', 'John', 'Acts', 'Rom', '1Cor', '2Cor', 'Gal', 'Eph', 'Phil',
    'Col', '1Thess', '2Thess', '1Tim', '2Tim', 'Titus', 'Phlm', 'Heb', 'Jas', '1Pet', '2Pet',
    '1John', '2John', '3John', 'Jude', 'Rev',
]
MY_BOOK_IDS = [
    'Mat', 'Mar', 'Luk', 'Jhn', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Phl',
    'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe', '2Pe',
    '1Jo', '2Jo', '3Jo', 'Jud', 'Rev',
]
MISSING_PREV_VERSE = {
    ('Matt', 17, 22),
    ('Matt', 18, 12),
    ('Matt', 23, 15),
    ('Mark', 7, 17),
    ('Mark', 9, 45),
    ('Mark', 9, 47),
    ('Mark', 11, 27),
    ('Mark', 15, 29),
    ('Luke', 17, 37),
    ('Luke', 23, 18),
    ('John', 5, 5),
    ('Acts', 8, 38),
    ('Acts', 15, 35),
    ('Acts', 24, 8),
    ('Acts', 28, 30),
}


def run():
    """Create a Greek New Testament from SBL OSIS file."""
    tree = _parse_xml()
    gnt = tree.findall('osisText/div')
    book, chapter, verse_tokens = [], [], []
    bcv = 'Matt', 1, 1
    prev_bcv = bcv
    for elem in tree.findall('osisText/div/*'):
        book, chapter, verse_tokens, bcv, prev_bcv = parse_osis_elem(
            elem, book, chapter, verse_tokens, bcv, prev_bcv)
    print('Writing {}'.format(prev_bcv[0]))
    _write_book(prev_bcv[0], book)


def _parse_xml():
    with open(os.path.join(GNT_DIR, '_cache', 'SBLGNT.osis.xml'), 'r') as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
        xmlstring = re.sub('</?list>', '', xmlstring)
        xmlstring = re.sub('</?item>', '', xmlstring)
        xmlstring = re.sub('</?lg?[^>]*>', '', xmlstring)
        xmlstring = re.sub('</?p[^>]*>', '', xmlstring)
    return ET.fromstring(xmlstring)


def parse_osis_elem(elem, book, chapter, verse_tokens, bcv, prev_bcv):
    """Parse OSIS element."""
    if elem.tag == 'verse' and 'osisID' in elem.attrib:
        bcv = _ref_to_bcv(elem.attrib['osisID'])

    if elem.tag == 'w' or (elem.tag == 'verse' and elem.tail):
        if bcv != prev_bcv and verse_tokens:
            if bcv in MISSING_PREV_VERSE:
                # Some verses are missing!
                chapter.append([])
            chapter.append(verse_tokens)
            verse_tokens = []
            if bcv[:2] != prev_bcv[:2]:
                book.append(chapter)
                chapter = []
                if bcv[:1] != prev_bcv[:1]:
                    print('Writing {}'.format(prev_bcv[0]))
                    _write_book(prev_bcv[0], book)
                    book = []
                elif bcv[1] != prev_bcv[1] + 1:
                    raise ValueError('Bad step {} {}'.format(prev_bcv, bcv))
            elif bcv[2] != prev_bcv[2] + 1 and bcv not in MISSING_PREV_VERSE:
                raise ValueError('Bad step {} {}'.format(prev_bcv, bcv))
            prev_bcv = bcv
        token = _parse_w_elem(elem)
        if token:
            verse_tokens.append(token)

    elif elem.tag == 'div':
        for sub_elem in elem.findall('*'):
            book, chapter, verse_tokens, bcv, prev_bcv = parse_osis_elem(
                sub_elem, book, chapter, verse_tokens, bcv, prev_bcv)

    return book, chapter, verse_tokens, bcv, prev_bcv


def _ref_to_bcv(ref):
    b, c, v = ref.split('.')
    return b, int(c), int(v)


def _parse_w_elem(elem):
    w = elem.text
    if w:
        w = w.lower()
        ws = _strip_accents(w)
        tlit = GREEK.transliterate(ws)
        strong = LOOKUP.get(ws)
        return w, ws, tlit, strong


def _write_book(os_id, text):
    id_map = dict(zip(OS_BOOK_IDS, MY_BOOK_IDS))
    with open(os.path.join(GNT_DIR, id_map[os_id] + '.json'), 'w') as f:
        json.dump({'text': text}, f)


def _strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


if __name__ == '__main__':
    run()