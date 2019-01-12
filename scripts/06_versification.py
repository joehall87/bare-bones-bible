import json
import os.path
import pickle
import re

import toml

_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_INPUT_FILE = os.path.join(_ROOT, 'resources', 'versification', 'versification.toml')
_OUTPUT_FILE = os.path.join(_ROOT, 'resources', 'versification', 'versification.pickle')


def run():
	"""Parse my toml file to produce a fast-access json."""
	with open(_INPUT_FILE, 'r') as f:
		blob = toml.load(f)
	versification = {}
	for book, counts in blob['verse-count'].items():
		num_verses = {c: count for c, count in enumerate(counts, start=1)}
		en_map = _make_en_map(book, blob, num_verses)
		en_disp = _make_en_disp(book, blob, en_map)
		versification[book] = {
			'num-chapters': len(counts),
			'num-verses': num_verses,
			'en-map': en_map, 
			'en-disp': en_disp,
		}
	with open(_OUTPUT_FILE, 'wb') as f:
		pickle.dump(versification, f)


def _make_en_map(book, blob, num_verses):
	en_map = {}
	# 1. Handle psalms
	if book == 'Psalms':
		for c in blob['psalm-titles']['one-verse-title']:
			for v in range(1, num_verses[c] + 1):
				en_map[(c, v)] = (c, v - 1)
		for c in blob['psalm-titles']['two-verse-title']:
			for v in range(1, num_verses[c] + 1):
				en_map[(c, v)] = (c, max(v - 2, 0))

	# 2. Handle rest
	else:
		for inp, out in blob['verse_map'].get(book, []):
			ic, iv1, iv2 = _parse(inp)
			oc, ov1, ov2 = _parse(out)
			# 1. Many -> One
			if iv1 < iv2 and ov1 == ov2:
				for v in range(iv1, iv2 + 1):
					en_map[(ic, v)] = (oc, ov1)
			# 2. One -> Many
			elif iv1 == iv2 and ov1 < ov2:
				en_map[(ic, iv1)] = (oc, ov1)  # Point to first one
			# 3. One -> One
			else:
				for iv, ov in zip(range(iv1, iv2 + 1), range(ov1, ov2 + 1)):
					en_map[(ic, iv)] = (oc, ov)
	return en_map


def _make_en_disp(book, blob, en_map):
	en_disp = {(ic, iv): str(ov) if ic == oc else '{}:{}'.format(oc, ov) for (ic, iv), (oc, ov) in en_map.items()}
	if book == 'Psalms':
		for c in blob['psalm-titles']['half-verse-title']:
			en_disp[(c, 1)] = '0-1'
	en_disp.update(_SPECIAL_CASES.get(book, {}))
	return en_disp


_SPECIAL_CASES = {
	'Exodus': {(20, 13): '13-16'},
	'Numbers': {(25, 19): '26:1a', (26, 1): '26:1b'},
	'Deuteronomy': {(5, 17): '17-20'},
	'Joshua': {(21, 35): '35-37'},
	'1 Samuel': {(20, 42): '20:42a', (21, 1): '20:42b'},
	'1 Kings': {(22, 43): '22:43a', (22, 44): '22:43b'},
	'Isaiah': {(63, 19): '63:19-64:1'},
	'Psalms': {(13, 6): '5-6'},
	'1 Chronicles': {(12, 4): "12:4a", (12, 5): '12:4b'},
}


def _parse(item):
	c, v1v2 = item.split(':')
	if '-' in v1v2:
		v1, v2 = v1v2.split('-')
	else:
		v1, v2 = v1v2, v1v2
	return int(c), int(v1), int(v2)



if __name__ == '__main__':
	run()