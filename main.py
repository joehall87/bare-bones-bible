import os.path
import re

from flask import Flask, render_template, redirect, request, url_for

from bibleapp.book import get_books


app = Flask(__name__)


@app.route('/')
def root():
    """Redirect to home."""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """Home page."""
    books = get_books()
    return render_template('home.html', page='home', dropdown=_get_dropdown(books))


@app.route('/book')
def book():
    """Show book."""
    books = get_books()
    code = request.args['book']
    book = [book for books in books.values() for book in books if book.code == code][0]
    start, end = None, None
    if 'chapter' in request.args:
        c = int(request.args['chapter'])
        start, end = (c, 0), (c, 999)
    return render_template('home.html', page='book', dropdown=_get_dropdown(books), book=book, cv_start=start, cv_end=end)


@app.route('/search')
def search():
    """Search for a range of text."""
    text = request.args['text'].strip()
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+):(\d+)$', text)  # Case 1: "book c1:v1 - c2:v2"
    if match:
        code  = match.group(1).lower()
        start = int(match.group(2)), int(match.group(3))
        end   = int(match.group(4)), int(match.group(5))
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)\s*-\s*(\d+)$', text)        # Case 2: "book c1:v1 - v2"
    if match:
        code  = match.group(1).lower()
        start = int(match.group(2)), int(match.group(3))
        end   = int(match.group(2)), int(match.group(4))
    match = re.match('^(\d?\w+)\s*(\d+):(\d+)$', text)                    # Case 3: "book c1:v1"
    if match:
        code  = match.group(1).lower()
        start = int(match.group(2)), int(match.group(3))
        end   = start
    match = re.match('^(\d?\w+)\s*(\d+)$', text)                          # Case 4: "book c1"
    if match:
        code  = match.group(1).lower()
        start = int(match.group(2)), 0
        end   = int(match.group(2)), 999
    match = re.match('^(\d?\w+)\s*(\d+)\s*-\s*(\d+)$', text)              # Case 5: "book c1 - c2"
    if match:
        code  = match.group(1).lower()
        start = int(match.group(2)), 0
        end   = int(match.group(3)), 999
    books = get_books()
    book = [book for books in books.values() for book in books if book.code == code][0]
    return render_template('home.html', page='book', dropdown=_get_dropdown(books), book=book, cv_start=start, cv_end=end)


def _get_dropdown(books):
    dropdown = []
    for part in ['Torah', 'Neviim', 'Ketuvim']:
        dropdown.append(('h5', 'header', part, ''))
        dropdown.extend([('a', 'item', book.name, 'href=/book?book={}'.format(book.code)) for book in books[part]])
        dropdown.append(('div', 'divider', '', ''))
    return dropdown[:-1]


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
