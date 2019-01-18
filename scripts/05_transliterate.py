import glob
import json
import os
import os.path
import re
import urllib.parse

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from b3.hebrew import Hebrew


_SEFARIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'sefaria')
_HEBREW = Hebrew()


def run():
	"""Create and store tokenised/transliterated hebrew."""
	for lan, fix_func in [('he', _tokenise_he_verse), ('en', _fix_en_verse)]:
		for path in glob.glob(os.path.join(_SEFARIA_DIR, '*.{}.json'.format(lan))):
			print('Parsing {}'.format(path))
			with open(path, 'r') as f:
				blob = json.load(f)
			blob['text'] = [[fix_func(verse) for verse in chapter] for chapter in blob['text']]
			with open(path.replace('.{}.'.format(lan), '.{}-parsed.'.format(lan)), 'w') as f:
				json.dump(blob, f)


def _fix_en_verse(verse):
	return re.sub('[Tt]he L[Oo][Rr][Dd](?: God)?', 'Yahweh', verse)


def _tokenise_he_verse(verse):
	tokens = []
	verse = verse.replace('\u200d', '')  # Random "zero-width joiners"!
	verse = _HEBREW.strip_cantillations(verse)
	for w, ws in _HEBREW.split_tokens(verse):
		wn = _HEBREW.strip_niqqud(w)
		tlit = _HEBREW.transliterate(w)
		tlit_s = _HEBREW.transliterate(ws)
		tokens.append((w, ws, wn, tlit, tlit_s))
	return tokens


if __name__ == '__main__':
	run()