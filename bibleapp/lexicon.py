from collections import defaultdict
import json
import os.path
import re
import urllib.parse

from bibleapp.hebrew import Hebrew

_HEBREW = Hebrew()
_BIBLE_HUB_LINK = '<a href="https://biblehub.com/hebrew/{id}.htm">H{id}</a>'
_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


class Lexicon(object):
	"""Wrapper around the Hebrew lexicon."""
	def __init__(self):
		self._lex = None
		self._refs = None

	@property
	def lex(self):
		"""Lexicon."""
		if self._lex is None:
			path = os.path.join(_RESOURCES_DIR, 'lexicon', 'Lexicon.json')
			with open(path, 'r') as f:
				self._lex = json.load(f)
		return self._lex

	@property
	def refs(self):
		"""Lexicon."""
		if self._refs is None:
			path = os.path.join(_RESOURCES_DIR, 'lexicon', 'References.json')
			with open(path, 'r') as f:
				self._refs = json.load(f)
		return self._refs

	def description(self, word):
		"""Return an html-description of the word."""
		desc = ''
		lex = self.lex.get(word)
		refs = self.refs.get(word)
		if not lex:
			return "<p>Can't find this word in lexicon.</p>"

		# 1. Google translate and refs
		root_lex = self.lex.get(lex['root'], {})
		root_refs = self.refs.get(lex['root'], {})
		if lex['trans']:
			desc += (
				"<p>Means <em>\"{}\"</em> according to Google and "
				"appears <strong>{}</strong> times in the Tanakh, first in {}. "
				.format(lex['trans'], len(refs), self._make_ref_link(refs[0]))
			)
			#root_trans = root.get('trans')
			#if trans != root_trans:
			#	refs_same_root = [ref for w in entry['variants'] for ref in self.map.get(w, {}).get('refs', [])]
			#	refs_same_root = sorted(entry['refs'] + refs_same_root, key=_ref_sort_key)
			#	desc += (
			#		"The root word <strong>{}</strong> <em>\"{}\"</em> appears "
			#		"<strong>{}</strong> times in {} different forms, first in {}."
			#		.format(entry['root'], root_trans, len(refs_same_root), len(entry['variants']) + 1, self._make_ref_link(refs_same_root[0]))
			#	)
			desc += '</p>'
		else:
			desc += "<p>Google doesn't know what this means!</p>"

		# 2. Strongs
		if lex['strongs']:
			item = lex['strongs']
			desc += "<hr/><p>[{url}] <strong>{word} {pron}</strong> - {desc}</p>".format(
				word=item['w'], pron=item['pron'], desc=item['desc'], url=_BIBLE_HUB_LINK.format(id=item['id'].strip('H')))

		return desc.replace('<def>', '<em>').replace('</def>', '</em>')

	@staticmethod
	def _make_ref_link(ref):
		pretty_ref = '{} {}:{}'.format(ref[0].title(), ref[1], ref[2])
		href = "/search?{}".format(urllib.parse.urlencode({'text': pretty_ref}))
		return '<a href="{href}">{ref}</a>'.format(ref=pretty_ref, href=href)


def _ref_sort_key(ref):
	book_num = [
		'gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jud', '1sam', '2sam', '1kin', '2kin', 'isa', 'jer', 'eze', 'hos', 'joe',
		'amo', 'oba', 'jon', 'mic', 'nah', 'hab', 'zep', 'hag', 'zec', 'mal', 'psa', 'pro', 'job', 'son', 'rut', 'lam', 
		'ecc', 'est', 'dan', 'ezr', 'neh', '1chr', '2chr',
	]
	return book_num.index(ref[0].lower()), ref[1], ref[2]
