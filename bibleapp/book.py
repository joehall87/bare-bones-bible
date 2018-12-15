import os
import os.path
import re


class Token(object):
	"""Token wrapper."""
	def __init__(self, word, space):
		self.word = word
		self.space = space


class Book(object):
	"""Wrapper around the Hebrew text for a book."""
	_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')

	def __init__(self, name):
		self.name = name
		self.file = '{}_{}'.format(name[2:], name[0]) if name[0].isdigit() else name.replace(' ', '_')
		self.code = name.replace(' ', '').lower()[:4 if name[0].isdigit() else 3]
		self.content = self._init_content()

	@property
	def num_chapters(self):
		"""Num chapters in book."""
		return self.content[-1][0]

	def iter_content(self, start=None, end=None):
		"""Iterate over content"""
		start = start or (0,0)
		end = end or (999,999)
		chapter, content = 0, []
		for c, v, tokens in self.content:
			if start <= (c, v) <= end:
				if c != chapter:
					if content:
						yield chapter, content
					chapter, content = c, []
				content.append((v, tokens))
		if content:
			yield chapter, content

	def iter_tokens(self, start=None, end=None):
		"""Iterate over content"""
		used = set()
		for chapter, content in self.iter_content(start, end):
			for v, tokens in content:
				for token in tokens:
					if token.word not in used:
						yield token
						used.add(token.word)

	def _init_content(self):
		path = os.path.join(self._RESOURCES_DIR, 'books', '{}.acc.txt'.format(self.file))
		with open(path, 'r') as f:
			lines = (line.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip() for line in f.readlines())
			return [self._parse_line(line) for line in lines if not line.startswith('xxxx')]

	@staticmethod
	def _parse_line(line):
		# Returns tuple of (chapter, verse, word_list)
		match = re.search('(\d+)\s*\u05C3(\d+)\s*(.*)', line)
		tokens = []
		for word in re.sub('[^\u0590-\u05FF ]', '', match.group(3)).split():  # Retain only Hebrew-unicode
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
		return int(match.group(2)), int(match.group(1)), tokens
