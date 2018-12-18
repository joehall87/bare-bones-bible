import html
import json
import os.path

# Setup guide: https://cloud.google.com/translate/docs/quickstart-client-libraries
from google.cloud import translate

from book import Tanakh


OPENSCRIPTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'openscriptures')


def run():
	"""Translate all words.

	Note
	----
	This will cost money! And may need to run a few times to get over request-rate limits.
	"""
	translations = {}
	json_path = os.path.join(OPENSCRIPTURES_DIR, 'GoogleTranslations.json')
	if os.path.exists(json_path):
		with open(json_path, 'r') as f:
			translations = json.load(f)

	tanakh = Tanakh()
	words = set()
	for book in tanakh.books:
		for _, verses in book.iter_verses_by_chapter():
			for verse in verses:
				for token in verse.he_tokens:
					if token.word_no_vowels not in translations:
						words.add(token.word_no_vowels)
	words = sorted(words)

	print('Translating {} words'.format(len(words)))
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
	
	with open(json_path, 'w') as f:
		json.dump(translations, f)


if __name__ == "__main__":
	run()
