from collections import defaultdict
import json
import os.path
import re
import urllib.parse


_BIBLE_HUB_LINK = '<a href="https://biblehub.com/hebrew/{id}.htm">H{id}</a>'


class Lexicon(object):
	"""Wrapper around the Hebrew lexicon."""
	def __init__(self):
		self._map = None

	@property
	def map(self):
		if self._map is None:
			path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'lexicon', 'CustomHebrewLexicon.json')
			with open(path, 'r') as f:
				self._map = json.load(f)
		return self._map

	def description(self, word):
		"""Return an html-description of the word."""
		desc = ''
		word = re.sub("[^\u05D0-\u05EA]", "", word)
		entry = self.map.get(word)

		# 1. Google translate
		trans = entry['trans']
		root = entry.get('root')
		if root:
			entry = self.map.get(root)
		if trans and root:
			desc += '<p><strong>{}</strong> means <em>"{}"</em> (according to Google), the root word is probably <strong>{}</strong>, which means <em>"{}"</em></p>'.format(
				word, trans, root, entry['trans'])
		elif trans:
			desc += '<p><strong>{}</strong> means <em>"{}"</em> (according to Google)</p>'.format(word, trans)
		else:
			desc += "<p>Google doesn't know what this means!</p>"

		# 2. References
		refs = entry.get('refs')
		if refs:
			variants = ['{} ({})'.format(v, self.map.get(v)['trans']) for v in entry['variants']]
			desc += (
				"<hr/><p>{root} first appears in {first} and is used <strong>{n}</strong> times in the Tanakh in the forms: {variants}".format(
					root=root or word, first=self._make_ref_link(refs[0]), n=len(refs), variants=' '.join(variants))
			)

		# 3. Strongs
		for i, item in enumerate(entry.get('strongs', [])):
			if i == 0:
				desc += '<hr/>'
			desc += "<p>[{url}] <strong>{word} {pron}</strong> - {desc}</p>".format(
				word=item['w'], pron=item['pron'], desc=item['desc'], url=_BIBLE_HUB_LINK.format(id=item['id'].strip('H')))

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
