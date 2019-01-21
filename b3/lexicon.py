from collections import defaultdict
import json
import os.path
import re
import urllib.parse


_STRONGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'strongs')


class Lexicon(object):
	"""Wrapper around the Hebrew lexicon."""
	def __init__(self):
		self._hebrew = None
		self._greek = None

	@property
	def hebrew(self):
		"""Hebrew Strongs."""
		if self._hebrew is None:
			self._hebrew = self._load('hebrew')
		return self._hebrew

	@property
	def greek(self):
		"""Greek Strongs."""
		if self._greek is None:
			self._greek = self._load('greek')
		return self._greek

	def get(self, strongs_id):
		"""Return an html-description of the word."""
		lookup = self.hebrew if strongs_id.startswith('H') else self.greek
		return lookup.get(strongs_id)

	@staticmethod
	def _load(lan):
		path = os.path.join(_STRONGS_DIR, lan + '.json')
		with open(path, 'r') as f:
			return json.load(f)
