import json
import os
import os.path
import re
import urllib.parse

from .hebrew import Hebrew


_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


_HEBREW = Hebrew()


class Tanakh():
	"""Wrapper around all books in Tanakh."""
	def __init__(self):
		self.books = [Book(x[0], x[1], bhub=x[2] if len(x) > 2 else None) for x in [
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
			('Ketuvim', 'Song of Songs', 'songs'),
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
			params = urllib.parse.urlencode({'name': book.name})
			dropdown.append(('a', 'item', book.name, 'href=/book?{}'.format(params)))
		return dropdown[1:]

	def get_book(self, alias):
		"""Get a specific book."""
		return [book for book in self.books if book.is_match(alias)][0]

	def search(self, search_str, book_filter=None, use='en'):
		"""Find a word or phrase."""
		occurrences, verses = 0, []
		search_obj = _make_search_obj(search_str, use=use)
		for book in self.books:
			if not book_filter or book.is_match(book_filter):
				for verse in book.iter_verses():
					num = verse.search(search_obj, use=use)
					if num:
						occurrences += num
						verses.append(verse)
		return occurrences, verses

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
			return self.get_book(name), start, end


class Book(object):
	"""Wrapper around the Hebrew text for a book."""

	def __init__(self, collection, name, bhub=None):
		self.collection = collection
		self.name = name
		self.bhub = bhub or name.replace(' ', '_').lower()
		self.he_name = None
		name = name.replace(' ', '').lower()
		if name[0].isdigit():
			num = name[0]
			name = name[1:]
			self.ref = num + name.title()[:3]
			self._aliases = set([num + name, name + num])
			self._aliases |= set(num + name[:i] for i in range(2, 6))
			self._aliases |= set(name[:i] + num for i in range(2, 6))
		else:
			self.ref = self.name[:3]
			self._aliases = set([name])
			self._aliases |= set(name[:i].lower() for i in range(2, 6))
		self._content = None

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
		return self.content[-1].c

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
		for lan in ['en', 'he']:
			path = os.path.join(_RESOURCES_DIR, 'sefaria', '{}.{}.json'.format(self.name, lan))
			with open(path, 'r') as f:
				blobs[lan] = json.load(f)
		self.he_name = blobs['he']['heTitle']
		for c, (en_chapter, he_chapter) in enumerate(zip(blobs['en']['text'], blobs['he']['text']), start=1):
			for v, (en_verse, he_verse) in enumerate(zip(en_chapter, he_chapter), start=1):
				content.append(Verse(self, c, v, en_verse, he_verse))
		return content


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, book, c, v, english, hebrew):
		self.book = book
		self.c = c
		self.v = v
		self.english = english
		for alias in ['the Lord', 'The Lord', 'the LORD', 'The LORD']:
			self.english = self.english.replace(alias, 'Yahweh')
		self.hebrew = _HEBREW.strip_cantillations(hebrew)
		self._he_tokens = None

	@property
	def ref(self):
		"""Pretty reference."""
		return '{} {}:{}'.format(self.book.ref, self.c, self.v)

	@property
	def bible_hub_url(self):
		"""The bible-hub url."""
		return "https://biblehub.com/lexicon/{b}/{c}-{v}.htm".format(
			b=self.book.bhub, c=self.c, v=self.v)

	def search(self, search_obj, use='en'):
		"""Search for an english or transliterated word/phrase."""
		if isinstance(search_obj, str):
			search_obj = _make_search_obj(search_obj)
		if use == 'en':
			num = len(search_obj.findall(self.english))
			if num:
				self.english = search_obj.sub('<span class="highlight">\g<1></span>', self.english)

		elif use == 'tlit':
			num = 0
			tokens = self.he_tokens
			n = len(search_obj)
			# Just looking for a single word
			if n == 1:
				for token in tokens:
					if search_obj[0] in token.tlit:
						token.highlight = True
						num += 1
			# Looking for multiple words
			else:
				for i in range(len(tokens) - n + 1):
					for j in range(n):
						if j == 0:
							success = tokens[i + j].tlit.endswith(search_obj[j])
						elif j < n - 1:
							success = tokens[i + j].tlit == search_obj[j]
						else:
							success = tokens[i + j].tlit.startswith(search_obj[j])
						if not success:
							break
					if success:
						num += 1
						for j in range(n):
							tokens[i + j].highlight = True
		return num

	@property
	def he_tokens(self):
		"""Hebrew tokens."""
		if not self._he_tokens:
			self._he_tokens = [Token(w, s) for w, s in _HEBREW.split_tokens(self.hebrew)]	
		return self._he_tokens


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None):
		self.word = word
		self.word_space = space
		self.word_no_vowels = _HEBREW.strip_niqqud(self.word)
		self.highlight = False

	@property
	def label(self):
		"""Html label."""
		return self.word

	@property
	def tlit(self):
		"""Transliteration."""
		return _HEBREW.transliterate(self.word)
	
	@property
	def tlit_space(self):
		"""Transliteration of space."""
		return _HEBREW.transliterate(self.word_space)


def _make_search_obj(search_str, use='en'):
	if use == 'en':
		return re.compile('({})'.format(search_str.replace('*', '\S*')), flags=re.IGNORECASE)
	else:
		return re.split('[\s\-:]', search_str.lower())
