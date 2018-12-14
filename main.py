import os.path
import re

from flask import Flask, render_template, request

from bibleapp.book import Book


app = Flask(__name__)


RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


torah = [
    Book('Genesis'),
    Book('Exodus'),
    Book('Leviticus'),
    Book('Numbers'),
    Book('Deuteronomy'),
]

neviim = [
    Book('Joshua'),
    Book('Judges'),
    Book('1 Samuel'),
    Book('2 Samuel'),
    Book('1 Kings'),
    Book('2 Kings'),
    Book('Isaiah'),
    Book('Jeremiah'),
    Book('Ezekial'),
    Book('Hosea'),
    Book('Joel'),
    Book('Amos'),
    Book('Obadiah'),
    Book('Jonah'),
    Book('Micah'),
    Book('Nahum'),
    Book('Habakkuk'),
    Book('Zephaniah'),
    Book('Haggai'),
    Book('Zechariah'),
    Book('Malachi'),
]

ketuvim = [
    Book('Psalms'),
    Book('Proverbs'),
    Book('Job'),
    Book('Song of Songs'),
    Book('Ruth'),
    Book('Lamentations'),
    Book('Ecclesiastes'),
    Book('Esther'),
    Book('Daniel'),
    Book('Ezra'),
    Book('Nehemiah'),
    Book('1 Chronicles'),
    Book('2 Chronicles'),
]


@app.route('/')
def root():
    """Show Tanakh"""
    #gen = os.path.join(RESOURCES_DIR, 'Books', 'Genesis.acc.txt')
    #with open(gen, 'r') as f:
    #    lines = (line.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip() for line in f.readlines())
    #    verses = [_parse_line(line) for line in lines if not line.startswith('xxxx')]
    dropdown = (
        [('h6', 'header', 'Torah',   '')] + [('a', 'item', book.name, 'href="#"') for book in torah] + [('div', 'divider', '', '')] +
        [('h6', 'header', 'Neviim',  '')] + [('a', 'item', book.name, 'href="#"') for book in neviim] + [('div', 'divider', '', '')] +
        [('h6', 'header', 'Ketuvim', '')] + [('a', 'item', book.name, 'href="#"') for book in ketuvim]
    )
    return render_template('home.html', dropdown=dropdown)


def _parse_line(line):
    match = re.search('(\d+)\s*\u05C3(\d+)\s*(.*)', line)
    return {'c': match.group(2), 'v': match.group(1), 'text': match.group(3)}


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
