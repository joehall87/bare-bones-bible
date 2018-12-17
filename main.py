import os.path
import re

from flask import Flask, render_template, redirect, request, url_for

from bibleapp.book import Book


app = Flask(__name__)


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
    Book('Ezekiel'),
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

dropdown = (
    [('h5', 'header', 'Torah',   '')] + [('a', 'item', book.name, 'href=/book?book={}'.format(book.code)) for book in torah] + [('div', 'divider', '', '')] +
    [('h5', 'header', 'Neviim',  '')] + [('a', 'item', book.name, 'href=/book?book={}'.format(book.code)) for book in neviim] + [('div', 'divider', '', '')] +
    [('h5', 'header', 'Ketuvim', '')] + [('a', 'item', book.name, 'href=/book?book={}'.format(book.code)) for book in ketuvim]
)


@app.route('/')
def root():
    """Redirect to home."""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """Home page."""
    return render_template('home.html', page='home', dropdown=dropdown)


@app.route('/book')
def book():
    """Show book."""
    code = request.args['book']
    book = [book for books in [torah, neviim, ketuvim] for book in books if book.code == code][0]
    start, end = None, None
    if 'chapter' in request.args:
        c = int(request.args['chapter'])
        start, end = (c, 0), (c, 999)
    return render_template('home.html', page='book', dropdown=dropdown, book=book, cv_start=start, cv_end=end)


@app.route('/search')
def search():
    """Search for a range of text."""
    text = request.args['text'].strip()
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+):(\d+)$', text)  # Case 1: "book c1:v1 - c2:v2"
    if match:
        code  = match.group(1)
        start = int(match.group(2)), int(match.group(3))
        end   = int(match.group(4)), int(match.group(5))
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+)$', text)        # Case 2: "book c1:v1 - v2"
    if match:
        code  = match.group(1)
        start = int(match.group(2)), int(match.group(3))
        end   = int(match.group(2)), int(match.group(4))
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)$', text)                    # Case 3: "book c1:v1"
    if match:
        code  = match.group(1)
        start = int(match.group(2)), int(match.group(3))
        end   = start
    match = re.match('^(\d?\w+)\s*(\d+)$', text)                          # Case 4: "book c1"
    if match:
        code  = match.group(1)
        start = int(match.group(2)), 0
        end   = int(match.group(2)), 999
    match = re.match('^(\d?\w+)\s*(\d+)\s*-\s*(\d+)$', text)              # Case 5: "book c1 - c2"
    if match:
        code  = match.group(1)
        start = int(match.group(2)), 0
        end   = int(match.group(3)), 999
    book = [book for books in [torah, neviim, ketuvim] for book in books if book.code == code][0]
    return render_template('home.html', page='book', dropdown=dropdown, book=book, cv_start=start, cv_end=end)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
