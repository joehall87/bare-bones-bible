import json
import os.path
import re
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from bibleapp.book import Tanakh


LEXICON_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'resources', 'lexicon')
BIBLEHUB_URL = 'https://biblehub.com/lexicon/{book}/{c}-{v}.htm'


def run():
	"""Scrape raw lexical data from biblehub."""
	if not os.path.exists(LEXICON_DIR):
		os.mkdir(LEXICON_DIR)
	for book in Tanakh().books:
		path = os.path.join(LEXICON_DIR, 'BibleHubScrape.{}.json'.format(book.name.replace(' ', '_')))
		if os.path.exists(path):
			with open(path, 'r') as f:
				data = json.load(f)['data']
				c_start = data[-1]['c']
				v_start = data[-1]['v'] + 1
		else:
			data = []
			c_start = 1
			v_start = 1
		for c in range(c_start, 1000):
			for v in range(v_start, 1000):
				url = BIBLEHUB_URL.format(book=book.bhub, c=c, v=v)
				try:
					success = True
					res = requests.get(url)
				except:
					success = False
					break
				if res.status_code == 404:
					break
				content = res.content.decode('utf-8')
				content = re.search('(<table[^>]+maintext[^>]+>.*?</table>)', content).group(0)
				data.append({'c': c, 'v': v, 'html': content, 'url': url})
				print('Loaded {b} {c}:{v}'.format(b=book.name, c=c, v=v))
			if v == 1:
				break
			v_start = 1
		with open(path, 'w') as f:
			json.dump({'data': data}, f)
		if not success:
			print('Think there was a connection error :(')
			break


if __name__ == "__main__":
	run()
	
