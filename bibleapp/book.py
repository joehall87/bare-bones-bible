import json
import os
import os.path
import re


class Book(object):
	"""Wrapper around the Hebrew text for a book."""
	_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')

	def __init__(self, name):
		self.name = name
		self.code = name.replace(' ', '').lower()[:4 if name[0].isdigit() else 3]
		self.he_content = self._init_he_content()

	@property
	def num_chapters(self):
		"""Num chapters in book."""
		return self.he_content[-1][0]

	def iter_verses_by_chapter(self, cv_start=None, cv_end=None):
		"""Iterate over verses"""
		cv_start = cv_start or (0,0)
		cv_end = cv_end or (999,999)
		chapter, verses = 0, []
		for c, verse in self.he_content:
			if cv_start <= (c, verse.num) <= cv_end:
				if c != chapter:
					if verses:
						yield chapter, verses
					chapter, verses = c, []
				verses.append(verse)
		if verses:
			yield chapter, verses

	def iter_tokens(self, cv_start=None, cv_end=None):
		"""Iterate over unique tokens."""
		used = set()
		for chapter, verses in self.iter_verses_by_chapter(cv_start, cv_end):
			for verse in verses:
				for token in verse.tokens:
					if token.word not in used:
						yield token
						used.add(token.word)

	def _init_he_content(self):
		content = []
		path = os.path.join(self._RESOURCES_DIR, 'sefaria', '{}.he.json'.format(self.name))
		with open(path, 'r') as f:
			blob = json.load(f)
			for c, verses in enumerate(blob['text'], start=1):
				for v, verse in enumerate(verses, start=1):
					content.append((c, self._parse_he_verse(v, verse)))
		return content

	@staticmethod
	def _parse_he_verse(v, verse):
		tokens = []
		for word in verse.split():
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
		return Verse(v, tokens)


class Verse(object):
	"""Verse wrapper."""
	def __init__(self, num, tokens):
		self.num = num
		self.tokens = tokens


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space=None):
		self.word = word
		self.space = space
