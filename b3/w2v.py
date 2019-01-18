import gensim.utils
import glob
import logging
import os
import re


logging.basicConfig(format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO)


BOOK_FILE_PATTERN = os.path.join(os.environ['HOME'], 'src', 'bible-app', 'resources', 'Tanach.con', '*.txt')


def parse_tanach():
    """Tokenize the Tanach"""
    logging.info("Reading the Tanach...this may take a while")
    for path in sorted(glob.glob(BOOK_FILE_PATTERN)):
        with open(path, 'r') as f:
            chapter = []
            for line in f.readlines():
                line = re.sub('[^\u05D0-\u05EA ]', '', line).strip()
                if line:
                    verse = gensim.utils.simple_preprocess(line)
                    chapter.extend(verse)
                elif chapter:
                    yield chapter


def train(epochs=10, size=100, window=10, min_count=2, workers=10):
    """Train a w2v model on the Tanach"""
    chapters = list(parse_tanach())
    model = gensim.models.Word2Vec(
        chapters,
        size=size,
        window=window,
        min_count=min_count,
        workers=workers)
    model.train(chapters, total_examples=len(chapters), epochs=epochs)
    return model


