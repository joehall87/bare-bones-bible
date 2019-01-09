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
		self._strongs = None
		self._lex = None
		self._lex_root = None

	@property
	def strongs(self):
		"""Strongs."""
		if self._strongs is None:
			self._strongs = self._load('Strongs.json')
		return self._strongs

	@property
	def lex(self):
		"""Lexicon."""
		if self._lex is None:
			self._lex = self._load('Lexicon.json')
		return self._lex

	@property
	def lex_root(self):
		"""Lexicon for root words."""
		if self._lex_root is None:
			self._lex_root = self._load('LexiconRoot.json')
		return self._lex_root

	def description(self, word):
		"""Return an html-description of the word."""
		desc = ''
		lex = self.lex.get(word)
		if not lex:
			return "<p>Can't find this word in lexicon.</p>"

		# 1. Google translate and refs
		lex_root = self.lex_root.get(lex['root'], {})
		desc += (
			"<p>Means <em>\"{}\"</em> according to Google and "
			"appears <strong>{}</strong> times in the Tanakh, first in {}. "
			.format(lex['trans'], len(lex['refs']), self._make_ref_link(lex['refs'][0]))
		)
		if lex['root-trans']:
			desc += (
				"The root word <strong>{}</strong> <em>\"{}\"</em> appears "
				"<strong>{}</strong> times, first in {}."
				.format(lex['root'], lex['root-trans'], len(lex_root['refs']), self._make_ref_link(lex_root['refs'][0]))
			)
		desc += '</p>'

		# 2. Strongs
		hr = '<hr/>'
		if lex['sid']:
			desc += hr + self._strongs_str(lex['sid'])
		other_sids = [sid for sid in lex_root.get('sids', []) if sid != lex['sid']]
		for sid in other_sids:
			desc += hr + self._strongs_str(sid)
			hr = ''

		return desc.replace('<def>', '<em>').replace('</def>', '</em>')

	def _strongs_str(self, sid):
		entry = self.strongs[sid]
		url = _BIBLE_HUB_LINK.format(id=entry['id'].strip('H'))
		return "<p>[{url}] <strong>{word} {pron}</strong> - {desc}</p>".format(
			word=entry['w'], pron=entry['pron'], desc=entry['desc'], url=url)

	@staticmethod
	def _make_ref_link(ref):
		pretty_ref = '{} {}:{}'.format(ref[0].title(), ref[1], ref[2])
		href = "/search?{}".format(urllib.parse.urlencode({'text': pretty_ref}))
		return '<a href="{href}">{ref}</a>'.format(ref=pretty_ref, href=href)

	@staticmethod
	def _load(resource):
		path = os.path.join(_RESOURCES_DIR, 'lexicon', resource)
		with open(path, 'r') as f:
			return json.load(f)


def _ref_sort_key(ref):
	book_num = [
		'gen', 'exo', 'lev', 'num', 'deu', 'jos', 'jud', '1sam', '2sam', '1kin', '2kin', 'isa', 'jer', 'eze', 'hos', 'joe',
		'amo', 'oba', 'jon', 'mic', 'nah', 'hab', 'zep', 'hag', 'zec', 'mal', 'psa', 'pro', 'job', 'son', 'rut', 'lam', 
		'ecc', 'est', 'dan', 'ezr', 'neh', '1chr', '2chr',
	]
	return book_num.index(ref[0].lower()), ref[1], ref[2]
