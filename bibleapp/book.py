import json
import os
import os.path
import re

from .lexicon import Lexicon


_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')
_CHARACTERS = '\u05D0-\u05EA'
_VOWELS = '\u05B0-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7'
_PUNCTUATION = '\u05BE\u05C0\u05C3\u05C6'  # Maqaf (-), Paseq (|), Sof Pasuq (:), Nun Hafukha
_CANTILLATIONS = '\u0591-\u05AF'


class Tanakh():
	"""Wrapper around all books in Tanakh."""
	def __init__(self):
		self.lexicon = Lexicon()
		self.books = [Book(collection, name, lexicon=self.lexicon) for collection, name in [
			('Torah', 'Genesis'),
			('Torah', 'Exodus'),
			('Torah', 'Leviticus'),
			('Torah', 'Numbers'),
			('Torah', 'Deuteronomy'),
			('Neviim', 'Joshua'),
			('Neviim', 'Judges'),
			('Neviim', '1 Samuel'),
			('Neviim', '2 Samuel'),
			('Neviim', '1 Kings'),
			('Neviim', '2 Kings'),
			('Neviim', 'Isaiah'),
			('Neviim', 'Jeremiah'),
			('Neviim', 'Ezekiel'),
			('Neviim', 'Hosea'),
			('Neviim', 'Joel'),
			('Neviim', 'Amos'),
			('Neviim', 'Obadiah'),
			('Neviim', 'Jonah'),
			('Neviim', 'Micah'),
			('Neviim', 'Nahum'),
			('Neviim', 'Habakkuk'),
			('Neviim', 'Zephaniah'),
			('Neviim', 'Haggai'),
			('Neviim', 'Zechariah'),
			('Neviim', 'Malachi'),
			('Ketuvim', 'Psalms'),
			('Ketuvim', 'Proverbs'),
			('Ketuvim', 'Job'),
			('Ketuvim', 'Song of Songs'),
			('Ketuvim', 'Ruth'),
			('Ketuvim', 'Lamentations'),
			('Ketuvim', 'Ecclesiastes'),
			('Ketuvim', 'Esther'),
			('Ketuvim', 'Daniel'),
			('Ketuvim', 'Ezra'),
			('Ketuvim', 'Nehemiah'),
			('Ketuvim', '1 Chronicles'),
			('Ketuvim', '2 Chronicles'),
		]]

	def get_dropdown(self):
		"""Get dropdown."""
		dropdown = []
		prev_collection = None
		for book in self.books:
			if book.collection != prev_collection:
				collection = prev_collection
				dropdown.append(('div', 'divider', '', ''))
				dropdown.append(('h5', 'header', collection, ''))
			dropdown.append(('a', 'item', book.name, 'href=/book?book={}'.format(book.code)))
		return dropdown[1:]

	def get_book(self, code):
		"""Get a specific book."""
		return [book for book in self.books if book.code == code.lower()][0]

	def get_passage(self, passage_str):
		"""Return the matching (book, cv_start, cv_end) tuple."""
		# Case 1: "book c1:v1 - c2:v2"
		match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+):(\d+)$', passage_str)
		if match:
			code  = match.group(1).lower()
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(4)), int(match.group(5))
		# Case 2: "book c1:v1 - v2"
		match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			code  = match.group(1).lower()
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(2)), int(match.group(4))
		# Case 3: "book c1:v1"
		match = re.match('^(\d?\w+)\s*(\d+):(\d+)$', passage_str)
		if match:
			code  = match.group(1).lower()
			start = int(match.group(2)), int(match.group(3))
			end   = start
		# Case 4: "book c1"
		match = re.match('^(\d?\w+)\s*(\d+)$', passage_str)						  
		if match:
			code  = match.group(1).lower()
			start = int(match.group(2)), 0
			end   = int(match.group(2)), 999
		# Case 5: "book c1 - c2"
		match = re.match('^(\d?\w+)\s*(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			code  = match.group(1).lower()
			start = int(match.group(2)), 0
			end   = int(match.group(3)), 999
		return self.get_book(code), start, end


class Book(object):
	"""Wrapper around the Hebrew text for a book."""

	def __init__(self, collection, name, lexicon=None):
		self.collection = collection
		self.name = name
		self.code = name.replace(' ', '').lower()[:4 if name[0].isdigit() else 3]
		self.lexicon = lexicon
		self._content = None

	@property
	def content(self):
		"""Memoize content."""
		if self._content is None:
			self._content = self._init_content()
		return self._content
	
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

	def iter_unique_he_tokens(self, cv_start=None, cv_end=None):
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
		return self._he_tokens	


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None, lexicon=None):
		self.word = word
		self.word_no_vowels = re.sub('[^{}]'.format(_CHARACTERS), '', self.word)
		self.space = space
		self.lexicon = lexicon

	@property
	def description(self):
		"""Description of word."""
		return self.lexicon.description(self.word)
