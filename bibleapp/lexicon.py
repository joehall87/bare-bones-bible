from collections import defaultdict
import json
import os.path
import re
import urllib.parse


_BLB_LINK = '<a href="https://www.blueletterbible.org/lang/lexicon/lexicon.cfm?t=kjv&strongs={id}">{id}</a>'


class Lexicon(object):
	"""Wrapper around the Hebrew lexicon."""
	_CHARACTERS = '\u05D0-\u05EA'

	def __init__(self):
		self._map = None
		self._map_clean = None

	@property
	def map(self):
		if self._map is None:
			path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'openscriptures', 'CustomHebrewLexicon.json')
			with open(path, 'r') as f:
				self._map = json.load(f)
		return self._map
	
	@property
	def map_clean(self):
		if self._map_clean is None:
			self._map_clean = defaultdict(list)
			for entry in self.map.values():
				self._map_clean[entry['w-clean']].append(entry)
		return self._map_clean

	def get(self, word):
		"""Get the entry for a word."""
		word = re.sub("[^{}]".format(self._CHARACTERS), "", word)
		return self.map_clean[word]

	def description(self, word):
		"""Return an html-description of the word."""
		desc = ''
		entries = self.get(word)

		# 1. Google translate
		if entries[0]['trans']:
			desc += '<p>Google says this means <em>"{}"</em></p>'.format(entries[0]['trans'])
		else:
			desc += "<p>Google doesn't know what this means!</p>"

		# 1. References
		allrefs = sorted([ref for entry in entries for ref in entry['refs']], key=_ref_sort_key)
		pretty_ref = lambda x: '{} {}:{}'.format(x[0].title(), x[1], x[2])
		desc += (
			"<hr/><p>It first appears in {first} and is used <strong>{n}</strong> times in the Tanakh in the following variants: {variants}.".format(
				first=self._make_ref_link(allrefs[0]), n=len(allrefs), variants=' '.join([x['w'] for x in entries])
		))

		# 3. Strongs
		for entry in entries:
			strongs = entry['strongs']
			if strongs:
				if strongs['meaning'] and strongs['usage']:
					info = strongs['meaning'] + '; ' + strongs['usage']
				else:
					info = strongs['meaning'] or strongs['usage']
				desc += "<hr/><p>[{url}] <strong>{word} {pron}</strong> - <em>{defn}</em> - {info}</p>".format(
					word=entry['w'], defn=entry['index']['def'], pron=strongs['pron'], info=info, url=_BLB_LINK.format(id=strongs['id']),
				)
			elif entry['index'].get('def'):
				desc += "<hr/><p><strong>{word}</strong> - <em>{defn}</em></p>".format(
					word=entry['w'], defn=entry['index']['def'],
				)
		return desc.replace('<def>', '<em>').replace('</def>', '</em>')

	@staticmethod
	def _make_ref_link(ref):
		pretty_ref = '{} {}:{}'.format(ref[0].title(), ref[1], ref[2])
		href = "/search?{}".format(urllib.parse.urlencode({'passage': pretty_ref}))
		return '<a href="{href}">{ref}</a>'.format(ref=pretty_ref, href=href)


def _ref_sort_key(ref):
	book_num = [
		'gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jud', '1sam', '2sam', '1kin', '2kin', 'isa', 'jer', 'eze', 'hos', 'joe',
		'amo', 'oba', 'jon', 'mic', 'nah', 'hab', 'zep', 'hag', 'zec', 'mal', 'psa', 'pro', 'job', 'son', 'rut', 'lam', 
		'ecc', 'est', 'dan', 'ezr', 'neh', '1chr', '2chr',
	]
	return book_num.index(ref[0]), ref[1], ref[2]
