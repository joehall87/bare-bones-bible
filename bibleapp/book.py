import json
import os
import os.path
import re

from .lexicon import Lexicon


def get_books():
	"""Get all books in Tanakh."""
	# TODO: Make this a class!!
	return {
		'Torah': [
		    Book('Genesis'),
		    Book('Exodus'),
		    Book('Leviticus'),
		    Book('Numbers'),
		    Book('Deuteronomy'),
		],
		'Neviim': [
		    Book('Joshua'),
		    Book('Judges'),
		    Book('1 Samuel'),
		    Book('2 Samuel'),
		    Book('1 Kings'),
		    Book('2 Kings'),
		    Book('Isaiah'),
		    Book('Jeremiah'),
		    Book('Ezekiel'),
		    Book('Hosea'),
		    Book('Joel'),
		    Book('Amos'),
		    Book('Obadiah'),
		    Book('Jonah'),
		    Book('Micah'),
		    Book('Nahum'),
		    Book('Habakkuk'),
		    Book('Zephaniah'),
		    Book('Haggai'),
		    Book('Zechariah'),
		    Book('Malachi'),
		],
		'Ketuvim': [
		    Book('Psalms'),
		    Book('Proverbs'),
		    Book('Job'),
		    Book('Song of Songs'),
		    Book('Ruth'),
		    Book('Lamentations'),
		    Book('Ecclesiastes'),
		    Book('Esther'),
		    Book('Daniel'),
		    Book('Ezra'),
		    Book('Nehemiah'),
		    Book('1 Chronicles'),
		    Book('2 Chronicles'),
		],
	}


_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
_CHARACTERS = '\u05D0-\u05EA'
_VOWELS = '\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7'
_PUNCTUATION = '\u05BE\u05C0\u05C3\u05C6'  # Maqaf (-), Paseq (|), Sof Pasuq (:), Nun Hafukha
_CANTILLATIONS = '\u0591-\u05AF'


class Book(object):
	"""Wrapper around the Hebrew text for a book."""

	def __init__(self, name):
		self.name = name
		self.code = name.replace(' ', '').lower()[:4 if name[0].isdigit() else 3]
		self._content = None
		self._lexicon = None

	@property
	def content(self):
		"""Memoize content."""
		if self._content is None:
			self._content = self._init_content()
		return self._content

	@property
	def lexicon(self):
		if self._lexicon is None:
			self._lexicon = Lexicon()
		return self._lexicon
	
	def _init_content(self):
		content = []
		blobs = {}
		for lan in ['en', 'he']:
			path = os.path.join(_RESOURCES_DIR, 'sefaria', '{}.{}.json'.format(self.name, lan))
			with open(path, 'r') as f:
				blobs[lan] = json.load(f)
		for c, (en_chapter, he_chapter) in enumerate(zip(blobs['en']['text'], blobs['he']['text']), start=1):
			for v, (en_verse, he_verse) in enumerate(zip(en_chapter, he_chapter), start=1):
				content.append((c, Verse(v, en_verse, he_verse, lexicon=self.lexicon)))
		return content

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


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, num, english, hebrew, lexicon=None):
		self.num = num
		self.english = english
		self.hebrew = hebrew
		self.lexicon = lexicon
		self._he_tokens = None

	@property
	def he_tokens(self):
		"""Hebrew tokens."""
		if self._he_tokens is None:
			self._he_tokens = []
			parts = re.sub('[{}]'.format(_CANTILLATIONS), '', self.hebrew).split()
			for word in parts:  # Remove cantillations
				space = ' '
				if word == '\u05C0':
					self._he_tokens[-1].space += '\u05C0 '
					continue
				if word[-1] == '\u05C3':
					word, space = word[:-1], '\u05C3'
				if '\u05BE' in word:
					parts = word.split('\u05BE')
					self._he_tokens.extend([Token(part, '\u05BE', lexicon=self.lexicon) for part in parts[:-1]])
					self._he_tokens.extend([Token(parts[-1], space, lexicon=self.lexicon)])
				else:
					self._he_tokens.append(Token(word, space, lexicon=self.lexicon))
			print(self._he_tokens)
		return self._he_tokens	


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None, lexicon=None):
		self.word = word
		self.space = space
		self.lexicon = lexicon

	@property
	def description(self):
		"""Description of word."""
		return self.lexicon.description(self.word)
