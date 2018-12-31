import json
import os
import os.path
import re

from .hebrew import Hebrew
from .lexicon import Lexicon


_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


_HEBREW = Hebrew()


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
				prev_collection = book.collection
				dropdown.append(('div', 'divider', '', ''))
				dropdown.append(('h5', 'header', book.collection, ''))
			dropdown.append(('a', 'item', book.name, 'href=/book?book={}'.format(book.code)))
		return dropdown[1:]

	def get_book(self, alias):
		"""Get a specific book."""
		return [book for book in self.books if book.is_match(alias)][0]

	def get_passage(self, passage_str):
		"""Return the matching (book, cv_start, cv_end) tuple."""
		# Case 1: "book c1:v1 - c2:v2"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+):(\d+)$', passage_str)
		if match:
			code  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(4)), int(match.group(5))
		# Case 2: "book c1:v1 - v2"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			code  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(2)), int(match.group(4))
		# Case 3: "book c1:v1"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)$', passage_str)
		if match:
			code  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = start
		# Case 4: "book c1"
		match = re.match('^([\w\s]+)\s+(\d+)$', passage_str)						  
		if match:
			code  = match.group(1)
			start = int(match.group(2)), 0
			end   = int(match.group(2)), 999
		# Case 5: "book c1 - c2"
		match = re.match('^([\w\s]+)\s+(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			code  = match.group(1)
			start = int(match.group(2)), 0
			end   = int(match.group(3)), 999
		return self.get_book(code), start, end


class Book(object):
	"""Wrapper around the Hebrew text for a book."""

	def __init__(self, collection, name, lexicon=None):
		self.collection = collection
		self.name = name
		self.lexicon = lexicon
		name = name.replace(' ', '').lower()
		if name[0].isdigit():
			num = name[0]
			name = name[1:]
			self.code = num + name[:3]
			self._aliases = set([num + name, name + num])
			self._aliases |= set(num + name[:i] for i in range(2, 6))
			self._aliases |= set(name[:i] + num for i in range(2, 6))
		else:
			self.code = name.lower()[:3]
			self._aliases = set([name])
			self._aliases |= set(name[:i].lower() for i in range(2, 6))
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
				content.append((c, Verse(self, c, v, en_verse, he_verse)))
		return content

	def is_match(self, alias):
		"""Does this alias match this book?"""
		return alias.replace(' ', '').lower() in self._aliases

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
			if cv_start <= (c, verse.v) <= cv_end:
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
	def __init__(self, book, c, v, english, hebrew):
		self.book = book
		self.c = c
		self.v = v
		self.english = english
		for alias in ['the Lord', 'The Lord', 'the LORD', 'The LORD']:
			self.english = self.english.replace(alias, 'Yahweh')
		self.hebrew = hebrew
		self.transliteration = _HEBREW.transliterate(hebrew)
		self._he_tokens = None

	@property
	def bible_hub_url(self):
		"""The bible-hub url."""
		return "https://biblehub.com/lexicon/{b}/{c}-{v}.htm".format(
			b=self.book.name.replace(' ', '_').lower(), c=self.c, v=self.v)

	@property
	def he_tokens(self):
		"""Hebrew tokens."""
		if self._he_tokens is None:
			self._he_tokens = []
			parts = _HEBREW.strip_cantillations(self.hebrew).split()
			for word in parts:  # Remove cantillations
				space = ' '
				if word == '\u05C0':
					self._he_tokens[-1].word_space += '\u05C0 '
					continue

				if word[0] in {'[', '(', '<'}:
					self._he_tokens[-1].word_space += ' ' + word[0]
					word = word[1:]

				if word[-1] in {'\u05C3', ']', ')', '>'}:
					word, space = word[:-1], word[-1] + ' '

				if '\u05BE' in word:
					parts = word.split('\u05BE')
					self._he_tokens.extend([Token(part, '\u05BE', lexicon=self.book.lexicon) for part in parts[:-1]])
					self._he_tokens.extend([Token(parts[-1], space, lexicon=self.book.lexicon)])
				else:
					self._he_tokens.append(Token(word, space, lexicon=self.book.lexicon))
		return self._he_tokens	


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None, lexicon=None):
		self.word = word
		self.word_space = space
		self.word_no_vowels = _HEBREW.strip_niqqud(self.word)
		self.lexicon = lexicon

	@property
	def tlit(self):
		"""Transliteration."""
		return _HEBREW.transliterate(self.word)
	
	@property
	def tlit_space(self):
		"""Transliteration of space."""
		return _HEBREW.transliterate(self.word_space)

	@property
	def description(self):
		"""Description of word."""
		return self.lexicon.description(self.word)
