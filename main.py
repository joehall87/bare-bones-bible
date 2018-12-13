import os.path
import re

from flask import Flask, render_template, request


app = Flask(__name__)


RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


class Book(object):
    def __init__(self, name, code):
        self.name = name
        self.code = code

torah = [
    Book('Genesis', 'gen'),
    Book('Exodus', 'exo'),
    Book('Leviticus', 'lev'),
    Book('Numbers', 'num'),
    Book('Deuteronomy', 'deu'),
]

neviim = [
    Book('Joshua', 'jos'),
    Book('Judges', 'jud'),
    Book('Samuel', 'sam'),
    Book('Kings', 'kin'),
    Book('Isaiah', 'isa'),
    Book('Jeremiah', 'jer'),
    Book('Ezekial', 'eze'),
    Book('The Twelve', 't12'),  # TODO Fix
]

ketuvim = [
    Book('Psalms', 'psa'),
    Book('Proverbs', 'pro'),
    Book('Job', 'job'),
    Book('Song of Songs', 'son'),
    Book('Ruth', 'rut'),
    Book('Lamentations', 'lam'),
    Book('Ecclesiastes', 'ecc'),
    Book('Esther', 'est'),
    Book('Daniel', 'dan'),
    Book('Ezra-Nehemiah', 'ezr'),
    Book('Chronicles', 'chr'),
]


@app.route('/')
def root():
    """Show Tanakh"""
    #gen = os.path.join(RESOURCES_DIR, 'Books', 'Genesis.acc.txt')
    #with open(gen, 'r') as f:
    #    lines = (line.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip() for line in f.readlines())
    #    verses = [_parse_line(line) for line in lines if not line.startswith('xxxx')]
    return render_template('home.html', torah=torah, neviim=neviim, ketuvim=ketuvim)


def _parse_line(line):
    match = re.search('(\d+)\s*\u05C3(\d+)\s*(.*)', line)
    return {'c': match.group(2), 'v': match.group(1), 'text': match.group(3)}


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
