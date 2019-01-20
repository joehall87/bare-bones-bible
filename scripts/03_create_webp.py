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
    book, chapter, verse_tokens = [], [], []
    title = None
    bcv = 'Gen', 1, 1
    prev_bcv = bcv
    for elem in ot.findall('div/div/*'):
        book, chapter, verse_tokens, title, bcv, prev_bcv = _parse_elem(
            elem, book, chapter, verse_tokens, title, bcv, prev_bcv)


def _parse_elem(elem, book, chapter, verse_tokens, title, bcv, prev_bcv):
    if elem.tag == 'verse' and 'osisID' in elem.attrib:
        bcv = _ref_to_bcv(elem.attrib['osisID'])

    elif elem.tag == 'title' and elem.attrib.get('type') == 'psalm':
        title = elem.text.strip()

    if elem.tag == 'w' or (elem.tag == 'verse' and elem.tail):
        if bcv != prev_bcv and verse_tokens:
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
            elif bcv[2] != prev_bcv[2] + 1:
                raise ValueError('Bad step {} {}'.format(prev_bcv, bcv))
            prev_bcv = bcv
        if title:
            verse_tokens.append(('', '[' + title + '] ', ''))
            title = None
        verse_tokens.append(_parse_w_elem(elem))

    elif elem.tag == 'div':
        for sub_elem in elem.findall('*'):
            book, chapter, verse_tokens, title, bcv, prev_bcv = _parse_elem(
                sub_elem, book, chapter, verse_tokens, title, bcv, prev_bcv)

    return book, chapter, verse_tokens, title, bcv, prev_bcv


def _parse_xml():
    with open(os.path.join(WEBP_DIR, '_cache', 'engwebp_osis.xml'), 'r') as f:
        xmlstring = re.sub(' xmlns="[^"]+"', '', f.read(), count=1)
        xmlstring = re.sub('</?list>', '', xmlstring)
        xmlstring = re.sub('</?item>', '', xmlstring)
        xmlstring = re.sub('</?lg?[^>]*>', '', xmlstring)
        xmlstring = re.sub('</?p[^>]*>', '', xmlstring)
    return ET.fromstring(xmlstring)


def _ref_to_bcv(ref):
    b, c, v = ref.split('.')
    return b, int(c), int(v)


def _parse_w_elem(elem):
    w = elem.text or ''
    seg = (elem.tail or ' ').replace('\n', ' ')
    strongs = elem.attrib.get('lemma', '').replace('strong:', '')
    return w, seg, strongs


def _write_book(os_id, text):
    id_map = dict(zip(OS_BOOK_IDS, MY_BOOK_IDS))
    with open(os.path.join(WEBP_DIR, id_map[os_id] + '.json'), 'w') as f:
        json.dump({'text': text}, f)


if __name__ == '__main__':
    run()