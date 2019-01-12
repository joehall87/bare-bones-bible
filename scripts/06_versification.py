import json
import re

import toml

_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_INPUT_FILE = os.path.join(_ROOT, 'resources', 'versification', 'versification.toml')
_OUTPUT_FILE = os.path.join(_ROOT, 'resources', 'versification', 'verse_map.json')


def run():
	"""Parse my toml file to produce a fast-access json."""
	with open(_TOML_FILE, 'r') as f:
		blob = toml.load(f)
	vm = {book: {'mismatch': {}, 'counts': counts} for book, counts in blob['verse-count'].items()}
	_extract_psalm_titles(vm, blob['psalm-titles'])
	_extract_mismatches(vm, blob['mismatches'])
	with open(_OUTPUT_FILE, 'w') as f:
		json.dump(vm, f)


def _extract_psalm_titles(vm, titles):
	counts = vm['Psalms']['counts']
	for c in titles['one-verse-title']:
		for v in range(1, counts[c - 1] + 1):
			vm['Psalms']['mismatch'][(c, v)] = (c, v - 1)
	for c in titles['two-verse-title']:
		for v in range(1, counts[c - 1] + 1):
			vm['Psalms']['mismatch'][(c, v)] = (c, max(v - 2, 0))


def _extract_mismatches(vm, one_to_one):
	for book, maps in one_to_one.items():
		for inp, out in maps:
			inp = _parse(inp)
			out = _parse(out)
			# 1. One -> One
			if inp[1] < inp[2] and out[1] < out[2]:
				(icv1, icv2), (ocv1, ocv2) = inp.split(' - '), out.split(' - ')
				ic1, iv1
			# 2. Many -> One
			elif inp[1] < inp[2]:
				pass
			# 3. One -> Many
			else:
				pass

def _parse(item):
	c, v1v2 = item.split(':')
	if '-' in v1v2:
		v1, v2 = v1v2.split('-')
	else:
		v1, v2 = v1v2, v1v2
	return int(c), int(v1), int(v2)



if __name__ == '__main__':
	run()