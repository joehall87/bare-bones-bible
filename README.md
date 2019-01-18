# bare-bones-bible
## Overview
The Bare Bones Bible (B3) project is a website designed to help budding Bible scholars
engage with the original Hebrew and Greek texts of the Bible.

## Local Setup
To get running locally do the following (basically following the QuickStart Python3 Standard environment docs from https://cloud.google.com/appengine/docs/standard/python3/quickstart):

```git clone https://github.com/joehall87/bare-bones-bible.git
cd bare-bones-bible
virtualenv --python=python3 env
source env/bin/activate
pip install  -r requirements.txt
python main.py
```

**Note:** It seems that `dev_appserver.py app.yaml` does not work with python3...so stick to `python main.py`.


## Resources
Follow the scripts in the `scripts` dir if you need to regenerate any of the resources.

