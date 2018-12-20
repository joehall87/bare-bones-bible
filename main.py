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
    print(request.args['book'])
    book = tanakh.get_book(request.args['book'])
    if 'chapter' in request.args:
        c = int(request.args['chapter'])
        start, end = (c, 0), (c, 999)
    else:
        start, end = None, None
    return render_template('home.html', page='book', dropdown=tanakh.get_dropdown(), book=book, cv_start=start, cv_end=end)


@app.route('/search')
def search():
    """Search for a range of text."""
    tanakh = Tanakh()
    passage_str = request.args['passage'].strip()
    book, start, end = tanakh.get_passage(passage_str)
    return render_template('home.html', page='book', dropdown=tanakh.get_dropdown(), book=book, cv_start=start, cv_end=end)


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
