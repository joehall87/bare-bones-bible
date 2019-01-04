import os.path
import re

from flask import Flask, render_template, redirect, request, url_for

from bibleapp.book import Tanakh
from bibleapp.lexicon import Lexicon


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
    lexicon = Lexicon()
    print(request.args['name'])
    book = tanakh.get_book(request.args['name'])
    chapter = request.args.get('chapter')
    kw = {'book': book, 'dropdown': tanakh.get_dropdown()}
    if not chapter:
        return render_template('home.html', page='chapter-select', **kw)
    else:
        c = int(chapter)
        title = '{} {}'.format(book.name, c)
        verses = list(book.iter_verses((c, None), (c, None)))
        modals = _create_modals(lexicon, verses)
        return render_template('home.html', page='chapter', chapter=c, verses=verses, modals=modals, **kw)


@app.route('/search')
def search():
    """Search for a range of text."""
    tanakh = Tanakh()
    lexicon = Lexicon()
    kw = {'dropdown': tanakh.get_dropdown()}
    search_str = request.args['text'].strip()

    # 1. Passage
    passage = tanakh.get_passage(search_str)
    if passage:
        book, start, end = passage
        verses = list(book.iter_verses(start, end))
        modals = _create_modals(lexicon, verses)
        kw.update({'verses': verses, 'modals': modals})
        if start[0] == end[0] and start[1] is None and end[1] is None:
            return render_template('home.html', page='chapter', book=book, chapter=start[0], **kw)
        else:
            title = _pretty_passage(book, start, end)
            return render_template('home.html', page='search-result', title=title, **kw)

    # 2. English or tlit phrase
    occurrences, verses = tanakh.search(search_str, use='en')
    #if not occurrences:
    #    occurrences, verses = tanakh.search(search_str, use='tlit')
    title = '{} <span style="font-size: 75%">occurrences of <span class="highlight">{}</span></span>'.format(occurrences, search_str)
    modals = _create_modals(lexicon, verses)
    return render_template('home.html', page='search-result', title=title, verses=verses, modals=modals, **kw)


def _pretty_passage(book, start, end):
    passage = book.name + ' '
    c1, v1 = start
    c2, v2 = end
    style = 'style="font-size: 75%"'
    if c1 == c2:
        passage += str(c1)
        if v1 and v2:
            if v1 == v2:
                passage += '<span {}>:{}</span>'.format(style, v1)
            else:
                passage += '<span {}>:{}-{}</span>'.format(style, v1, v2)
    elif v1 and v2:
        passage += '{}<span {}>:{}</span>-{}<span {}>:{}</span>'.format(c1, style, v1, c2, style, v2)
    else:
        passage += '{}-{}'.format(c1, c2)
    return passage


def _create_modals(lexicon, verses):
    modals, used = [], set()
    for verse in verses:
        for token in verse.he_tokens:
            if token.word not in used:
                desc = lexicon.description(token.word)
                modals.append((token, desc))
                used.add(token.word)
    return modals


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
