import json
import os
import os.path
import pickle
import re


_VERSE_URL = "https://www.blueletterbible.org/kjv/{b}/{c}/{v}/t_conc_{c_abs}{v_zfill}"
_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')


class Bible():
	"""Wrapper around all books in the Bible."""
	@property
	def books(self):
		"""Make books lazy to free-up mem."""
		return [Book(x[0], x[1], x[2], x[3], code=x[4] if len(x) > 4 else None) for x in _BOOKS]

	def get_book(self, alias):
		"""Get a specific book."""
		books = [book for book in self.books if book.is_match(alias)]
		if not books:
			raise UnknownBookError('I can\'t find a book matching <strong>"{}"</strong>.<br>Please try again.'.format(alias))
		return books[0]

	def search_strongs(self, id_, start=None, end=None, book_filter=None):
		"""Find occurrences by strongs reference."""
		num_occurrences, num_verses, verses = 0, 0, []
		for book in self._iter_books(book_filter):
			for verse in book.iter_verses():
				num = verse.search_strongs(id_)
				if num:
					if start <= num_verses < end:
						verses.append(verse)
					num_occurrences += num
					num_verses += 1
		return num_occurrences, num_verses, verses

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
		# Case 0: "book"
		try:
			book = self.get_book(passage_str)
			name = book.name
			start = 1, None
			end = 1, None
		except UnknownBookError:
			pass
		# Case 1: "book c1:v1 - c2:v2"
		if not name:
			match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+):(\d+)$', passage_str)
			if match:
				name  = match.group(1)
				start = int(match.group(2)), int(match.group(3))
				end   = int(match.group(4)), int(match.group(5))
		# Case 2: "book c1:v1 - v2"
		if not name:
			match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)\s*-\s*(\d+)$', passage_str)
			if match:
				name  = match.group(1)
				start = int(match.group(2)), int(match.group(3))
				end   = int(match.group(2)), int(match.group(4))
		# Case 3: "book c1:v1"
		if not name:
			match = re.match('^([\w\s]+)\s+(\d+)\:(\d+)$', passage_str)
			if match:
				name  = match.group(1)
				start = int(match.group(2)), int(match.group(3))
				end   = start
		# Case 4: "book c1"
		if not name:
			match = re.match('^([\w\s]+)\s+(\d+)$', passage_str)						  
			if match:
				name  = match.group(1)
				start = int(match.group(2)), None
				end   = int(match.group(2)), None
		# Case 5: "book c1 - c2"
		if not name:
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

	def __init__(self, collection, name, num_chapters, ch_offset, code=None):
		self.collection = collection
		self.name = name
		self.num_chapters = num_chapters
		self.ch_offset = ch_offset
		self.code = code or name.replace(' ', '')[:3]
		self.is_nt = collection not in {'Torah', 'Neviim', 'Ketuvim'}
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
		# Prevent conflicts
		if name == 'Judges':
			self._aliases.pop('ju')  # Jude
			self._aliases.pop('jud')
		elif name in {'Job', 'Joel'}:
			self._aliases.pop('jo')  # John
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
		codexes = [self._load_codex(x)['text'] for x in (['webp', 'gnt'] if self.is_nt else ['webp', 'lxx', 'wlc'])]
		for c, chapters in enumerate(zip(*codexes), start=1):
			for v, verses in enumerate(zip(*chapters), start=1):
				if self.is_nt:
					args = [EnToken(*x) for x in verses[0]], [GrToken(*x) for x in verses[1]]
				else:
					args = [EnToken(*x) for x in verses[0]], [GrToken(*x) for x in verses[1]], [HeToken(*x) for x in verses[2]]
				verse = Verse(self, c, v, *args)
				content.append(verse)
		return content

	def _load_codex(self, codex):
		path = os.path.join(_RESOURCES_DIR, codex, self.code + '.json')
		with open(path, 'r') as f:
			return json.load(f)


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, book, c, v, english_tokens, greek_tokens, hebrew_tokens=None):
		self.book = book
		self.c = c
		self.v = v
		self.en_tokens = english_tokens
		self.gr_tokens = greek_tokens
		self.he_tokens = hebrew_tokens

	def ref(self, verse_only=False):
		"""Pretty reference."""
		if verse_only:
			return '{}'.format(self.v)
		else:
			return '{} {}:{}'.format(self.book.code, self.c, self.v)

	@property
	def url(self):
		"""The bible-hub url."""
		return _VERSE_URL.format(b=self.book.code.lower(), c=self.c, v=self.v, 
			c_abs=self.book.ch_offset + self.c, v_zfill=str(self.v).zfill(3))

	def search_strongs(self, id_):
		"""Search a strongs reference."""
		num = 0
		if id_.startswith('H') and self.he_tokens is None:
			return num
		tokens = self.he_tokens if id_.startswith('H') else self.gr_tokens
		for token in tokens:
			if token.strongs == id_:
				token.highlight = True
				num += 1
		for token in self.en_tokens:
			if token.strongs == id_:
				token.highlight = True
		return num

	def search(self, search_obj, lang='en'):
		"""Search for an english or transliterated word/phrase."""
		num = 0
		if isinstance(search_obj, str):
			search_obj = _make_search_obj(search_obj)
		if not lang or lang == 'en':
			num += self._search_tokens(search_obj, self.en_tokens)
		if not lang or lang == 'gr':
			num += self._search_tokens(search_obj, self.gr_tokens)
		if not lang or lang == 'he':
			num += self._search_tokens(search_obj, self.he_tokens or [])
		return num

	def _search_tokens(self, search_obj, tokens):
		num = 0
		n = len(search_obj)
		for i in range(len(tokens) - n + 1):
			for j, obj in enumerate(search_obj):
				success = obj.match(tokens[i + j].word_to_search)
				if not success:
					break
			if success:
				num += 1
				for j in range(n):
					tokens[i + j].highlight = True
		return num


class EnToken(object):
	"""Token wrapper."""
	def __init__(self, word, word_space, strongs):
		self.word = word
		self.word_space = word_space
		self.strongs = strongs
		self.word_to_search = word
		self.highlight = False
	

class HeToken(object):
	"""Token wrapper."""
	def __init__(self, word, word_no_vowels, tlit, strongs, word_space, tlit_space):
		self.word = word
		self.word_no_vowels = word_no_vowels
		self.tlit = tlit
		self.strongs = strongs
		self.word_space = word_space
		self.tlit_space = tlit_space
		self.word_to_search = tlit
		self.highlight = False

	def to_display(self):
		"""Nice html display."""
		disp = _to_display('hebrew', self.word, self.tlit, self.strongs, self.highlight)
		if self.word_space:
			disp += """
        <table class="mini-table">
          <tr><td><p style="line-height: 140%">
            <span class="hebrew">{word_space}</span>
            <br>
            <span class="translit" dir='ltr'>{tlit_space}</span>
          </p></td></tr>
        </table>""".format(word_space=self.word_space, tlit_space=self.tlit_space)
		return disp


class GrToken(object):
	"""Token wrapper."""
	def __init__(self, word, word_no_vowels, tlit, strongs):
		self.word = word
		self.word_no_vowels = word_no_vowels
		self.tlit = tlit
		self.strongs = strongs
		self.word_to_search = tlit
		self.highlight = False

	def to_display(self):
		"""Nice html display."""
		return _to_display('greek', self.word_no_vowels, self.tlit, self.strongs, self.highlight, lh='130%')


def _to_display(lan, word, tlit, strongs, highlight, lh='140%'):
	if strongs:
		word_disp = (
			'<a href="#" data-toggle="modal" data-target="#{strongs}">'
			'<span {highlight}>{word}</span></a>'
		).format(
			strongs=strongs,
			word=word,
			highlight='class="highlight"' if highlight else '',
		)
	else:
		word_disp = (
			'<span {highlight}>{word}</span>'
		).format(
			word=word,
			highlight='class="highlight"' if highlight else 'style="color:grey"',
		)
	tlit_disp = word_disp.replace(word, tlit)
	return """<table class="mini-table">
      <tr><td><p style="line-height: {lh}">
        <span class="{lan}">
          {word_disp}
        </span>
        <br>
        <span class="translit" dir='ltr'>
          {tlit_disp}
        </span>
      </p></td></tr>
    </table>""".format(lan=lan, word_disp=word_disp, tlit_disp=tlit_disp, lh=lh)


def _make_search_obj(search_str):
	search_str = search_str.replace('.', '\\.')
	re_list = []
	for term in re.split('[\s\-:]', search_str.lower()):
		re_list.append(re.compile('^{}$'.format(term.replace('*', '.*'))))
	return re_list


class UnknownBookError(Exception):
	pass


_BOOKS = [
	('Torah', 'Genesis', 50, 0),
	('Torah', 'Exodus', 40, 50),
	('Torah', 'Leviticus', 27, 90),
	('Torah', 'Numbers', 36, 117),
	('Torah', 'Deuteronomy', 34, 153),
	('Neviim', 'Joshua', 24, 187),
	('Neviim', 'Judges', 21, 211, 'Jdg'),
	('Neviim', '1 Samuel', 31, 236),
	('Neviim', '2 Samuel', 24, 267),
	('Neviim', '1 Kings', 22, 291),
	('Neviim', '2 Kings', 25, 313),
	('Neviim', 'Isaiah', 66, 679),
	('Neviim', 'Jeremiah', 52, 745),
	('Neviim', 'Ezekiel', 48, 802),
	('Neviim', 'Hosea', 14, 862),
	('Neviim', 'Joel', 3, 876),
	('Neviim', 'Amos', 9, 879),
	('Neviim', 'Obadiah', 1, 888),
	('Neviim', 'Jonah', 4, 889),
	('Neviim', 'Micah', 7, 893),
	('Neviim', 'Nahum', 3, 900),
	('Neviim', 'Habakkuk', 3, 903),
	('Neviim', 'Zephaniah', 3, 906),
	('Neviim', 'Haggai', 2, 909),
	('Neviim', 'Zechariah', 14, 911),
	('Neviim', 'Malachi', 4, 925),
	('Ketuvim', 'Psalms', 150, 478),
	('Ketuvim', 'Proverbs', 31, 628),
	('Ketuvim', 'Job', 42, 436),
	('Ketuvim', 'Song of Songs', 8, 671, 'Sng'),
	('Ketuvim', 'Ruth', 4, 232, 'Rth'),
	('Ketuvim', 'Lamentations', 5, 797),
	('Ketuvim', 'Ecclesiastes', 12, 659),
	('Ketuvim', 'Esther', 10, 426),
	('Ketuvim', 'Daniel', 12, 850),
	('Ketuvim', 'Ezra', 10, 403),
	('Ketuvim', 'Nehemiah', 13, 413),
	('Ketuvim', '1 Chronicles', 29, 338),
	('Ketuvim', '2 Chronicles', 36, 367),
	('Gospels', 'Matthew', 28, 921),
	('Gospels', 'Mark', 16, 957),
	('Gospels', 'Luke', 24, 973),
	('Gospels', 'John', 21, 997, 'Jhn'),
	('History', 'Acts', 28, 1018),
	('Pauline Epistles', 'Romans', 16, 1046),
	('Pauline Epistles', '1 Corinthians', 16, 1062),
	('Pauline Epistles', '2 Corinthians', 13, 1078),
	('Pauline Epistles', 'Galatians', 6, 1091),
	('Pauline Epistles', 'Ephesians', 6, 1097),
	('Pauline Epistles', 'Philippians', 4, 1103, 'Phl'),
	('Pauline Epistles', 'Colossians', 4, 1107),
	('Pauline Epistles', '1 Thessalonians', 5, 1111),
	('Pauline Epistles', '2 Thessalonians', 3, 1116),
	('Pauline Epistles', '1 Timothy', 6, 1119),
	('Pauline Epistles', '2 Timothy', 4, 1125),
	('Pauline Epistles', 'Titus', 3, 1129),
	('Pauline Epistles', 'Philemon', 1, 1132, 'Phm'),
	('General Epistles', 'Hebrews', 13, 1133),
	('General Epistles', 'James', 5, 1146, 'Jas'),
	('General Epistles', '1 Peter', 5, 1151),
	('General Epistles', '2 Peter', 3, 1156),
	('General Epistles', '1 John', 5, 1159),
	('General Epistles', '2 John', 1, 1164),
	('General Epistles', '3 John', 1, 1165),
	('General Epistles', 'Jude', 1, 1166),
	('Apocalyptic', 'Revelation', 22, 1167),
]
