import math
import os.path
import re
import urllib.parse

from flask import Flask, render_template, redirect, request, url_for

from bibleapp.book import Tanakh, UnknownBookError
from bibleapp.lexicon import Lexicon


app = Flask(__name__)


SEARCH_LIMIT = 100


@app.route('/')
def root():
    """Redirect to home."""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """Home page."""
    return render_template('home.html', page='home')


@app.route('/book')
def book():
    """Show book."""
    name = request.args['name']
    chapter = request.args.get('chapter')
    try:
        return _make_chapter(name, int(chapter)) if chapter else _make_chapter_select(name)
    except UnknownBookError as e:
        return render_template('home.html', page='error', msg=str(e))


@app.route('/search')
def search():
    """Search for a range of text."""
    search_str = request.args['text'].strip()
    pag_page = int(request.args.get('page', 1))
    try:
        return _search(search_str, pag_page)
    except UnknownBookError as e:
        return render_template('home.html', page='error', msg=str(e))


@app.errorhandler(404)
def page_not_found(e):
    """Nice 404 error."""
    return render_template('home.html', page='error', msg="That page doesn't exist!"), 404


def _make_chapter(name, chapter):
    tanakh = Tanakh()
    lexicon = Lexicon()
    book = tanakh.get_book(name)
    title = '{} {}'.format(book.name, chapter)
    verses = list(book.iter_verses((chapter, None), (chapter, None)))
    modals = _create_modals(lexicon, verses)
    return render_template('home.html', page='chapter', book=book, chapter=chapter, verses=verses, modals=modals)


def _make_chapter_select(name):
    tanakh = Tanakh()
    book = tanakh.get_book(name)
    return render_template('home.html', page='chapter-select', book=book)


def _search(search_str, pag_page):
    tanakh = Tanakh()
    lexicon = Lexicon()
    kw = {'search_value': search_str}
    search_str, options = _extract_options(search_str)

    # 1. Passage
    passage = tanakh.get_passage(search_str)
    if passage:
        name, start, end = passage
        book = tanakh.get_book(name)
        verses = list(book.iter_verses(start, end))
        modals = _create_modals(lexicon, verses)
        kw.update({'verses': verses, 'modals': modals})
        if start[0] == end[0] and start[1] is None and end[1] is None:
            return render_template('home.html', page='chapter', book=book, chapter=start[0], **kw)
        else:
            title = _pretty_passage(book, start, end)
            return render_template('home.html', page='search-result', title=title, **kw)

    # 2. English or tlit phrase
    occurrences, verses = 0, []
    book_filter = options.get('book', options.get('books'))
    lang = {
        'he': 'he', 
        'heb': 'he', 
        'hebrew': 'he',
        'en': 'en',
        'eng': 'en',
        'english': 'en',
    }.get(options.get('lang', options.get('lan')))
    occurrences, verses = tanakh.search(search_str, book_filter=book_filter, lang=lang)
    title = '{} <span style="font-size: 75%">occurrences of <span class="highlight">{}</span></span>'.format(
        occurrences, search_str)
    modals = _create_modals(lexicon, verses)
    verses = _paginate(verses, pag_page, kw)
    return render_template('home.html', page='search-result', title=title, verses=verses, modals=modals, 
        book_filter=tanakh.pretty_book_filter(book_filter), **kw)


def _extract_options(search_str):
    options = {}
    new_str_list = []
    for part in search_str.split():
        kv = part.split(':')
        if len(kv) == 2 and kv[0].lower() in {'book', 'books', 'lan', 'lang'}:
            options[kv[0].lower()] = kv[1]
        else:
            new_str_list.append(part)
    return ' '.join(new_str_list), options


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


def _paginate(verses, pag_page, kw):
    if len(verses) <= SEARCH_LIMIT:
        return verses

    n = len(verses)
    start = (pag_page - 1) * SEARCH_LIMIT
    end = min(pag_page * SEARCH_LIMIT, n)
    verses = verses[start:end]

    n_pages = int(math.ceil(n / SEARCH_LIMIT))
    pagination = []
    href_func = lambda pg: "/search?{}".format(urllib.parse.urlencode({'text': kw['search_value'], 'page': pg}))
    for i in range(1, n_pages + 1):
        pagination.append({
            'symbol': i,
            'class': 'active' if i == pag_page else '',
            'href': href_func(i),
        })
    previous = {
        'symbol': '&laquo;',
        'class': 'disabled' if pag_page == 1 else '',
        'href': href_func(pag_page - 1),
    }
    next_ = {
        'symbol': '&raquo;',
        'class': 'disabled' if pag_page == n_pages else '',
        'href': href_func(pag_page + 1),
    }
    kw['pagination'] = [previous] + pagination + [next_]
    return verses


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
