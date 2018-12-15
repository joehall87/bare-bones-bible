import os.path
import re

from flask import Flask, render_template, request

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
    [('h5', 'header', 'Torah',   '')] + [('a', 'item', book.name, 'href=/?book={}'.format(book.code)) for book in torah] + [('div', 'divider', '', '')] +
    [('h5', 'header', 'Neviim',  '')] + [('a', 'item', book.name, 'href=/?book={}'.format(book.code)) for book in neviim] + [('div', 'divider', '', '')] +
    [('h5', 'header', 'Ketuvim', '')] + [('a', 'item', book.name, 'href=/?book={}'.format(book.code)) for book in ketuvim]
)


@app.route('/')
def root():
    """Show Tanakh"""
    book = None
    code = request.args.get('book')
    if code:
        book = [book for books in [torah, neviim, ketuvim] for book in books if book.code == code][0]
    return render_template('home.html', dropdown=dropdown, book=book)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
