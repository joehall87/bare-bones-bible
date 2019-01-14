import json
import os
import os.path
import pickle
import re

from .hebrew import Hebrew


_VERSE_URL = "https://www.blueletterbible.org/kjv/{b}/{c}/{v}/t_conc_{c_abs}{v_zfill}"
_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


_HEBREW = Hebrew()
with open(os.path.join(_RESOURCES_DIR, 'versification', 'versification.pickle'), 'rb') as f:
	_VERSIFICATION = pickle.load(f)


class Tanakh():
	"""Wrapper around all books in Tanakh."""
	@property
	def books(self):
		"""Make books lazy to free-up mem."""
		return [Book(x[0], x[1], x[2], code=x[3] if len(x) > 3 else None) for x in _BOOKS]

	def get_book(self, alias):
		"""Get a specific book."""
		books = [book for book in self.books if book.is_match(alias)]
		if not books:
			raise UnknownBookError('I can\'t find a book matching <strong>"{}"</strong>.<br>Please try again.'.format(alias))
		return books[0]

	def search(self, search_str, start=None, end=None, book_filter=None, lang=None):
		"""Find a word or phrase."""
		search_obj = _make_search_obj(search_str)
		num_occurrences, num_verses, verses = 0, 0, []
		for book in self._iter_books(book_filter):
			for verse in book.iter_verses():
				num = verse.search(search_obj, lang=lang)
				if num:
					if start <= num_verses < end:
						verses.append(verse)
					num_occurrences += num
					num_verses += 1
		return num_occurrences, num_verses, verses

	def get_passage(self, passage_str):
		"""Return the matching (book, cv_start, cv_end) tuple."""
		name = None
		# Case 1: "book c1:v1 - c2:v2"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+):(\d+)$', passage_str)
		if match:
			name  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(4)), int(match.group(5))
		# Case 2: "book c1:v1 - v2"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			name  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = int(match.group(2)), int(match.group(4))
		# Case 3: "book c1:v1"
		match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)$', passage_str)
		if match:
			name  = match.group(1)
			start = int(match.group(2)), int(match.group(3))
			end   = start
		# Case 4: "book c1"
		match = re.match('^([\w\s]+)\s+(\d+)$', passage_str)						  
		if match:
			name  = match.group(1)
			start = int(match.group(2)), None
			end   = int(match.group(2)), None
		# Case 5: "book c1 - c2"
		match = re.match('^([\w\s]+)\s+(\d+)\s*-\s*(\d+)$', passage_str)
		if match:
			name  = match.group(1)
			start = int(match.group(2)), None
			end   = int(match.group(3)), None
		if name:
			return name, start, end

	def pretty_book_filter(self, book_filter):
		"""Make a pretty string."""
		if book_filter:
			pretty_parts = []
			for part in book_filter.split(','):
				if '-' in part:
					start, end = part.split('-')
					pretty_parts.append('{} - {}'.format(self.get_book(start).name, self.get_book(end).name))
				else:
					pretty_parts.append(self.get_book(part).name)
			pretty = ', '.join(pretty_parts)
			return ' & '.join(pretty.rsplit(', '))
		else:
			return 'the Tanakh'

	def _iter_books(self, book_filter):
		if book_filter:
			for part in book_filter.split(','):
				if '-' in part:
					start, end = part.split('-')
					in_range = False
					for book in self.books:
						if not in_range and book.is_match(start):
							in_range = True
							yield book
						elif in_range:
							yield book
							if book.is_match(end):
								break
				else:
					yield self.get_book(part)
		else:
			for book in self.books:
				yield book


class Book(object):
	"""Wrapper around the Hebrew text for a book."""

	def __init__(self, collection, name, ch_offset, code=None):
		self.collection = collection
		self.name = name
		self.code = code or name.replace(' ', '')[:3]
		self.he_name = None
		name = name.replace(' ', '').lower()
		if name[0].isdigit():
			num = name[0]
			name = name[1:]
			self._aliases = set([num + name, name + num])
			self._aliases |= set(num + name[:i] for i in range(2, 6))
			self._aliases |= set(name[:i] + num for i in range(2, 6))
		else:
			self._aliases = set([name])
			self._aliases |= set(name[:i].lower() for i in range(2, 6))
		self._content = None
		self.ch_offset = ch_offset

	@property
	def content(self):
		"""Memoize content."""
		if self._content is None:
			self._content = self._init_content()
		return self._content

	def is_match(self, alias):
		"""Does this alias match this book?"""
		return alias.replace(' ', '').lower() in self._aliases

	@property
	def num_chapters(self):
		"""Num chapters in book."""
		return _VERSIFICATION[self.name]['num-chapters']

	def iter_verses(self, cv_start=None, cv_end=None):
		"""Iterate over verses"""
		c1 = 0 if not cv_start or not cv_start[0] else cv_start[0]
		v1 = 0 if not cv_start or not cv_start[1] else cv_start[1]
		c2 = 999 if not cv_end or not cv_end[0] else cv_end[0]
		v2 = 999 if not cv_end or not cv_end[1] else cv_end[1]
		for verse in self.content:
			if (c1, v1) <= (verse.c, verse.v) <= (c2, v2):
				yield verse
	
	def _init_content(self):
		content = []
		blobs = {}
		for lan in ['en-parsed', 'he-parsed']:
			path = os.path.join(_RESOURCES_DIR, 'sefaria', '{}.{}.json'.format(self.name, lan))
			with open(path, 'r') as f:
				blobs[lan] = json.load(f)
		self.he_name = blobs['he-parsed']['heTitle']
		for c, (en_chapter, he_chapter) in enumerate(zip(blobs['en-parsed']['text'], blobs['he-parsed']['text']), start=1):
			for v, (en_verse, he_verse) in enumerate(zip(en_chapter, he_chapter), start=1):
				verse = Verse(self, c, v, en_verse, [Token(*args) for args in he_verse])
				content.append(verse)
		return content


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, book, c, v, english, hebrew_tokens):
		self.book = book
		self.c = c
		self.v = v
		self.english = english
		self.he_tokens = hebrew_tokens

	def ref(self, verse_only=False):
		"""Pretty reference."""
		suffix = _VERSIFICATION[self.book.name]['en-disp'].get((self.c, self.v), '')
		if suffix:
			suffix = '<small>({})</small>'.format(suffix)
		if verse_only:
			return '{}{}'.format(self.v, suffix)
		else:
			return '{} {}:{}{}'.format(self.book.code, self.c, self.v, suffix)

	@property
	def url(self):
		"""The bible-hub url."""
		c, v = _VERSIFICATION[self.book.name]['en-map'].get((self.c, self.v), (self.c, self.v))
		return _VERSE_URL.format(b=self.book.code.lower(), c=c, v=v, 
			c_abs=self.book.ch_offset + c, v_zfill=str(v).zfill(3))

	def search(self, search_obj, lang='en'):
		"""Search for an english or transliterated word/phrase."""
		num = 0
		if isinstance(search_obj, str):
			search_obj = _make_search_obj(search_obj)

		if not lang or lang == 'en':
			num += len(search_obj['en'].findall(self.english))
			if num:
				self.english = search_obj['en'].sub('<span class="highlight">\g<1></span>', self.english)

		if not lang or lang == 'he':
			tokens = self.he_tokens
			n = len(search_obj['he'])
			for i in range(len(tokens) - n + 1):
				for j, obj in enumerate(search_obj['he']):
					success = obj.match(tokens[i + j].tlit)
					if not success:
						break
				if success:
					num += 1
					for j in range(n):
						tokens[i + j].highlight = True
		return num


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, word_space, word_no_vowels, tlit, tlit_space):
		self.word = word
		self.word_space = word_space
		self.word_no_vowels = word_no_vowels
		self.tlit = tlit
		self.tlit_space = tlit_space
		self.highlight = False

	@property
	def label(self):
		"""Html label."""
		return self.word


def _make_search_obj(search_str, lang='en'):
	search_str = search_str.replace('.', '\\.')
	en_re_expr = re.compile('({})'.format(search_str.replace('*', '\S*')), flags=re.IGNORECASE)
	he_re_list = []
	for term in re.split('[\s\-:]', search_str.lower()):
		he_re_list.append(re.compile(term.replace('*', '.*')))
	return {
		'en': en_re_expr,
		'he': he_re_list,
	}


class UnknownBookError(Exception):
	pass


_BOOKS = [
	('Torah', 'Genesis', 0),
	('Torah', 'Exodus', 50),
	('Torah', 'Leviticus', 90),
	('Torah', 'Numbers', 117),
	('Torah', 'Deuteronomy', 153),
	('Neviim', 'Joshua', 187),
	('Neviim', 'Judges', 211, 'Jdg'),
	('Neviim', '1 Samuel', 236),
	('Neviim', '2 Samuel', 267),
	('Neviim', '1 Kings', 291),
	('Neviim', '2 Kings', 313),
	('Neviim', 'Isaiah', 679),
	('Neviim', 'Jeremiah', 745),
	('Neviim', 'Ezekiel', 802),
	('Neviim', 'Hosea', 862),
	('Neviim', 'Joel', 876),
	('Neviim', 'Amos', 879),
	('Neviim', 'Obadiah', 888),
	('Neviim', 'Jonah', 889),
	('Neviim', 'Micah', 893),
	('Neviim', 'Nahum', 900),
	('Neviim', 'Habakkuk', 903),
	('Neviim', 'Zephaniah', 906),
	('Neviim', 'Haggai', 909),
	('Neviim', 'Zechariah', 911),
	('Neviim', 'Malachi', 925),
	('Ketuvim', 'Psalms', 478),
	('Ketuvim', 'Proverbs', 628),
	('Ketuvim', 'Job', 436),
	('Ketuvim', 'Song of Songs', 671, 'Sng'),
	('Ketuvim', 'Ruth', 232, 'Rth'),
	('Ketuvim', 'Lamentations', 797),
	('Ketuvim', 'Ecclesiastes', 659),
	('Ketuvim', 'Esther', 426),
	('Ketuvim', 'Daniel', 850),
	('Ketuvim', 'Ezra', 403),
	('Ketuvim', 'Nehemiah', 413),
	('Ketuvim', '1 Chronicles', 338),
	('Ketuvim', '2 Chronicles', 367),
]
