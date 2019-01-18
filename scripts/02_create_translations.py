import html
import json
import os.path
import re

import bs4
# Setup guide: https://cloud.google.com/translate/docs/quickstart-client-libraries
from google.cloud import translate

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from b3.book import Tanakh


LEXICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'lexicon')


def run():
	"""Translate all words.

	Note
	----
	This will cost money! And may need to run a few times to get over request-rate limits.
	"""
	print('1. Load what we already have')
	translations = {}
	json_path = os.path.join(LEXICON_DIR, 'GoogleTranslations.json')
	if os.path.exists(json_path):
		with open(json_path, 'r') as f:
			translations = json.load(f)

	print('2. Fetch all words (and sub-words) from Tanakh')
	tanakh = Tanakh()
	words = set()
	for book in tanakh.books:
		for _, verses in book.iter_verses_by_chapter():
			for verse in verses:
				for token in verse.he_tokens:
					w = token.word_no_vowels
					for i, j in [(None, None), (None, -1), (1, None), (1, -1)]:
						if w[i:j] not in translations:
							words.add(w[i:j])

	print('3. Fetch all words available in Strongs')
	with open(os.path.join(LEXICON_DIR, 'LexicalIndex.xml'), 'r') as f:
		index = bs4.BeautifulSoup(f.read(), 'html.parser')
	for entry in index.find_all('entry'):
		w = re.sub('[^\u05D0-\u05EA]', '', entry.find('w').contents[0])
		if w not in translations:
			words.add(w)
	words = sorted(words)

	print("4. Translating {} words".format(len(words)))
	client = translate.Client()
	chunk = 100
	try:
		for i in range(0, len(words), chunk):
			print('Batch {}'.format(i))
			batch = words[i:i + chunk]
			results = client.translate(batch, source_language='he', target_language='en')
			for word, trans in zip(batch, [html.unescape(x['translatedText']) for x in results]):
				translations[word] = trans if word != trans else None
	except Exception as e:
		print(e)
	
	print('5. Persist')
	with open(json_path, 'w') as f:
		json.dump(translations, f)


if __name__ == "__main__":
	run()
