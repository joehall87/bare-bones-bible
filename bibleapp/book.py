import json
import os
import os.path
import re

from .lexicon import Lexicon


LEXICON = Lexicon()


class Book(object):
	"""Wrapper around the Hebrew text for a book."""
	_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
	_CHARACTERS = '\u05D0-\u05EA'
	_VOWELS = '\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7'
	_PUNCTUATION = '\u05BE\u05C0\u05C3\u05C6'  # Maqaf (-), Paseq (|), Sof Pasuq (:), Nun Hafukha
	_CANTILLATIONS = '\u0591-\u05AF'

	def __init__(self, name):
		self.name = name
		self.code = name.replace(' ', '').lower()[:4 if name[0].isdigit() else 3]
		self.content = self._init_content()

	@property
	def num_chapters(self):
		"""Num chapters in book."""
		return self.content[-1][0]

	def iter_verses_by_chapter(self, cv_start=None, cv_end=None):
		"""Iterate over verses"""
		cv_start = cv_start or (0,0)
		cv_end = cv_end or (999,999)
		chapter, verses = 0, []
		for c, verse in self.content:
			if cv_start <= (c, verse.num) <= cv_end:
				if c != chapter:
					if verses:
						yield chapter, verses
					chapter, verses = c, []
				verses.append(verse)
		if verses:
			yield chapter, verses

	def iter_he_tokens(self, cv_start=None, cv_end=None):
		"""Iterate over unique tokens."""
		used = set()
		for chapter, verses in self.iter_verses_by_chapter(cv_start, cv_end):
			for verse in verses:
				for token in verse.he_tokens:
					if token.word not in used:
						yield token
						used.add(token.word)

	def _init_content(self):
		content = []
		blobs = {}
		for lan in ['en', 'he']:
			path = os.path.join(self._RESOURCES_DIR, 'sefaria', '{}.{}.json'.format(self.name, lan))
			with open(path, 'r') as f:
				blobs[lan] = json.load(f)
		for c, (en_verses, he_verses) in enumerate(zip(blobs['en']['text'], blobs['he']['text']), start=1):
			for v, (en_verse, he_verse) in enumerate(zip(en_verses, he_verses), start=1):
				content.append((c, self._parse_verse(v, en_verse, he_verse)))
		return content

	def _parse_verse(self, v, en_verse, he_verse):
		tokens = []
		for word in re.sub('[{}]'.format(self._CANTILLATIONS), '', he_verse).split():  # Remove cantillations
			space = ' '
			if word == '\u05C0':
				tokens[-1].space += '\u05C0 '
				continue
			if word[-1] == '\u05C3':
				word, space = word[:-1], '\u05C3'
			if '\u05BE' in word:
				parts = word.split('\u05BE')
				tokens.extend([Token(part, '\u05BE') for part in parts[:-1]] + [Token(parts[-1], space)])
			else:
				tokens.append(Token(word, space))
		return Verse(v, en_verse, tokens)


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, num, english, he_tokens):
		self.num = num
		self.english = english
		self.he_tokens = he_tokens


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None):
		self.word = word
		self.space = space

	@property
	def description(self):
		"""Description of word."""
		return LEXICON.description(self.word)
