import os
import os.path
import re


class Book(object):
	"""Wrapper around the Hebrew text for a book."""
	_RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources')

	def __init__(self, name):
		self.name = name
		self.file = '{}_{}'.format(name[2:], name[0]) if name[0].isdigit() else name.replace(' ', '_')
		self.code = name.replace(' ', '').lower()[:3]
		self.content = self._init_content()

	def iter_content(self, start=(0,0), end=(999,999)):
		"""Iterate over content"""
		new_chapter = True
		for c, v, words in self.content:
			yield c, v, words

	def _init_content(self):
		path = os.path.join(self._RESOURCES_DIR, 'books', '{}.acc.txt'.format(self.file))
		with open(path, 'r') as f:
			lines = (line.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip() for line in f.readlines())
			return [self._parse_line(line) for line in lines if not line.startswith('xxxx')]

	@staticmethod
	def _parse_line(line):
		# Returns tuple of (chapter, verse, word_list)
		match = re.search('(\d+)\s*\u05C3(\d+)\s*(.*)', line)
		return int(match.group(2)), int(match.group(1)), match.group(3).split()
