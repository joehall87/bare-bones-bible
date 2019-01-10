import glob
import json
import os
import os.path
import re
import urllib.parse

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from bibleapp.hebrew import Hebrew


_SEFARIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'sefaria')


def run():
	"""Create and store tokenised/transliterated hebrew."""
	heb = Hebrew()
	for path in glob.glob(os.path.join(_SEFARIA_DIR, '*.he.json')):
		print('Parsing {}'.format(path))
		with open(path, 'r') as f:
			blob = json.load(f)
		blob['text'] = [[list(_parse_verse(verse, heb)) for verse in chapter] for chapter in blob['text']]
		with open(path.replace('.he.', '.he-parsed.'), 'w') as f:
			json.dump(blob, f)


def _parse_verse(verse, heb):
	verse = heb.strip_cantillations(verse)
	for w, ws in heb.split_tokens(verse):
		wn = heb.strip_niqqud(w)
		tlit = heb.transliterate(w)
		tlit_s = heb.transliterate(ws)
		yield w, ws, wn, tlit, tlit_s


if __name__ == '__main__':
	run()