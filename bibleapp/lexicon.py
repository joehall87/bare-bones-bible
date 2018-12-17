from collections import defaultdict
import json
import os.path
import re


_BLB_LINK = '<a href="https://www.blueletterbible.org/lang/lexicon/lexicon.cfm?t=kjv&strongs={id}">{id}</a>'


class Lexicon(object):
	"""Wrapper around the Hebrew lexicon."""
	_CHARACTERS = '\u05D0-\u05EA'

	def __init__(self):
		path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'openscriptures', 'CustomHebrewLexicon.json')
		with open(path, 'r') as f:
			self.map = json.load(f)
		self.char_only_map = defaultdict(list)
		for word, entry in sorted(self.map.items()):
			word = re.sub("[^{}]".format(self._CHARACTERS), "", word)
			self.char_only_map[word].append(entry)

	def get(self, word):
		"""Get the entry for a word."""
		word = re.sub("[^{}]".format(self._CHARACTERS), "", word)
		return self.char_only_map[word]

	def description(self, word):
		"""Return an html-description of the word."""
		descs = []
		for entry in self.get(word):
			strong = entry['strong']
			if strong:
				if strong['meaning'] and strong['usage']:
					info = strong['meaning'] + '; ' + strong['usage']
				else:
					info = strong['meaning'] or strong['usage']
				descs.append("<strong>{word} {pron}</strong> - <em>{defn}</em> - {info} [{url}]".format(
					word=entry['w'], defn=entry['def'], pron=strong['pron'], info=info, url=_BLB_LINK.format(id=strong['id']),
				))
			elif entry['def']:
				descs.append("<strong>{word}</strong> - <em>{defn}</em>".format(
					word=entry['w'], defn=entry['def'],
				))
		desc = '</p><p>'.join(desc.replace('<def>', '<em>').replace('</def>', '</em>') for desc in descs)
		return '<p>{}</p>'.format(desc or "Sorry, couldn't find any info on this.")
