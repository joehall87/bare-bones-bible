# bible-app
## Overview
Awesome code to search the Hebrew Tanakh.

## Local Setup
To get running locally do the following (basically following the QuickStart Python3 Standard environment docs from https://cloud.google.com/appengine/docs/standard/python3/quickstart):

```git clone https://github.com/joehall87/bible-app.git
cd bible-app
virtualenv --python=python3 env
source env/bin/activate
pip install  -r requirements.txt
python main.py
```

Tanach resources can be downloaded from: http://www.tanach.us/TextFiles/Tanach.acc.txt.zip...currently only utilising the raw \*.acc.txt files.

**Note:** It seems that `dev_appserver.py app.yaml` does not work with python3...so stick to `python main.py`.
