import json
import os
import os.path
import requests

books = [
    # Torah
    'Genesis',
    'Exodus',
    'Leviticus',
    'Numbers',
    'Deuteronomy',
    # Neviim
    'Joshua',
    'Judges',
    '1 Samuel',
    '2 Samuel',
    '1 Kings',
    '2 Kings',
    'Isaiah',
    'Jeremiah',
    'Ezekiel',
    'Hosea',
    'Joel',
    'Amos',
    'Obadiah',
    'Jonah',
    'Micah',
    'Nahum',
    'Habakkuk',
    'Zephaniah',
    'Haggai',
    'Zechariah',
    'Malachi',
    # Ketuvim
    'Psalms',
    'Proverbs',
    'Job',
    'Song of Songs',
    'Ruth',
    'Lamentations',
    'Ecclesiastes',
    'Esther',
    'Daniel',
    'Ezra',
    'Nehemiah',
    '1 Chronicles',
    '2 Chronicles',
]


SEFARIA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'sefaria')
SEFARIA_URL = 'https://www.sefaria.org/download/version/{book} - {lan} - merged.json'


def run():
	"""Download resources from the awesome www.sefaria.org."""
	if not os.path.exists(SEFARIA_DIR):
		os.mkdir(SEFARIA_DIR)
	for book in books:
		for lan in ['he', 'en']:
			print('Fetching {} [{}]'.format(book, lan))
			path = os.path.join(SEFARIA_DIR, '{}.{}.json'.format(book, lan))
			resp = requests.get(SEFARIA_URL.format(book=book.replace('1', 'I').replace('2', 'II'), lan=lan))
			with open(path, 'w') as f:
				json.dump(resp.json(), f)


if __name__ == "__main__":
	run()
	
