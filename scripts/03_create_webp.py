import json
import os
import os.path
import re
import sys
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(ROOT_DIR)

import xml.etree.ElementTree as ET


# Assumes you have downloaded engwebp_osis.zip from http://ebible.org/find/details.php?id=engwebp&all=1
# and extracted the .xml file into resources/webp/_cache
WEBP_DIR = os.path.join(ROOT_DIR, 'resources', 'webp')

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
    """Create a parsed English Bible from the freely available World English Bible."""
    tree = _parse_xml()
    ot, nt = tree.findall('osisText/div')
    id_map = dict(zip(OS_BOOK_IDS, MY_BOOK_IDS))
    book, chapter, verse_tokens = [], [], []
    prev_bcv = 'Gen', 1, 1
    # TODO!!! Also fetch the psalms which live in div/div/div/*!!
    for elem in ot.findall('div/div/*'):
        if elem.tag == 'verse' and 'osisID' in elem.attrib:
            bcv = _ref_to_bcv(elem.attrib['osisID'])
        elif elem.tag == 'w':
            if bcv != prev_bcv and verse_tokens:
                chapter.append(verse_tokens)
                verse_tokens = []
                if bcv[:2] != prev_bcv[:2]:
                    book.append(chapter)
                    chapter = []
                    if bcv[:1] != prev_bcv[:1]:
                        print('Writing {}'.format(prev_bcv[0]))
                        _write_book(id_map[prev_bcv[0]], book)
                        book = []
                prev_bcv = bcv
            verse_tokens.append(_parse_w_elem(elem))


def _parse_xml():
    with open(os.path.join(WEBP_DIR, '_cache', 'engwebp_osis.xml'), 'r') as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
        xmlstring = re.sub('</?lg?[^>]*>', '', xmlstring)
        xmlstring = re.sub('</?p[^>]*>', '', xmlstring)
    return ET.fromstring(xmlstring)


def _ref_to_bcv(ref):
    b, c, v = ref.split('.')
    return b, int(c), int(v)


def _parse_w_elem(elem):
    w = elem.text
    seg = (elem.tail or ' ').replace('\n', ' ')
    strongs = elem.attrib['lemma'].replace('strong:', '')
    return w, seg, strongs


def _write_book(name, text):
    with open(os.path.join(WEBP_DIR, name + '.json'), 'w') as f:
        json.dump({'text': text}, f)


if __name__ == '__main__':
    run()