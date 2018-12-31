import os.path
import re

from flask import Flask, render_template, redirect, request, url_for

from bibleapp.book import Tanakh


app = Flask(__name__)


@app.route('/')
def root():
    """Redirect to home."""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """Home page."""
    return render_template('home.html', page='home', dropdown=Tanakh().get_dropdown())


@app.route('/book')
def book():
    """Show book."""
    tanakh = Tanakh()
    print(request.args['name'])
    book = tanakh.get_book(request.args['name'])
    chapter = request.args.get('chapter')
    kw = {'book': book, 'dropdown': tanakh.get_dropdown()}
    if not chapter:
        return render_template('home.html', page='chapter-select', title=book.name, **kw)
    else:
        c = int(chapter)
        title = '{} {}'.format(book.name, c)
        verses = list(book.iter_verses((c, None), (c, None)))
        tokens = list(book.iter_unique_he_tokens((c, None), (c, None)))
        return render_template('home.html', page='chapter', title=title, verses=verses, tokens=tokens, **kw)


@app.route('/search')
def search():
    """Search for a range of text."""
    tanakh = Tanakh()
    search_str = request.args['text'].strip()
    passage = tanakh.get_passage(search_str)
    if passage:
        book, start, end = passage
        title = _pretty_passage(book, start, end)
        verses = list(book.iter_verses(start, end))
        tokens = list(book.iter_unique_he_tokens(start, end))
        kw = {'book': book, 'title': title, 'verses': verses, 'tokens': tokens, 'dropdown': tanakh.get_dropdown()}
        if start[0] == end[0] and start[1] is None and end[1] is None:
            return render_template('home.html', page='chapter', **kw)
        else:
            return render_template('home.html', page='search-result', **kw)
    return 'Nooooo!'


def _pretty_passage(book, start, end):
    passage = book.name + ' '
    c1, v1 = start
    c2, v2 = end
    style = 'style="font-size: 75%"'
    if c1 == c2:
        passage += str(c1)
        if v1 and v2 and v1 == v2:
            passage += '<span {}>:{}</span>'.format(style, v1)
        elif v1 < v2:
            passage += '<span {}>:{}-{}</span>'.format(style, v1, v2)
    elif v1 and v2:
        passage += '{}<span {}>:{}</span>-{}<span {}>:{}</span>'.format(c1, style, v1, c2, style, v2)
    else:
        passage += '{}-{}'.format(c1, c2)
    return passage


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
