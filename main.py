import os.path
import re

from flask import Flask, render_template, request


app = Flask(__name__)


RESOURCES_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'resources')


@app.route('/')
def root():
    """Show Tanach"""
    gen = os.path.join(RESOURCES_DIR, 'Books', 'Genesis.acc.txt')
    with open(gen, 'r') as f:
        lines = (line.replace('\u202a', '').replace('\u202b', '').replace('\u202c', '').strip() for line in f.readlines())
        verses = [_parse_line(line) for line in lines if not line.startswith('xxxx')]
    return render_template('root.html', verses=verses)


def _parse_line(line):
    match = re.search('(\d+)\s*\u05C3(\d+)\s*(.*)', line)
    return {'c': match.group(2), 'v': match.group(1), 'text': match.group(3)}


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
