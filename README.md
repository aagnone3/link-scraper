# Link Scraper

## Setup
This software uses [Selenium]() with a headless Chromium browser for the automation.
You can obtain a new version of the Chromium web driver [here](https://chromedriver.chromium.org/downloads), they consistently release newer and better versions.

Recommended setup: keep multiple versions at a time, and use a symbolic link (assuming OSX/Linux) to specify the version to use:
```bash
# example: /usr/local/bin is on your $PATH
# have the following:
# - /usr/local/bin/chromedriver81
# - /usr/local/bin/chromedriver82
# - /usr/local/bin/chromedriver83
ln -s /usr/local/bin/chromedriver83 /usr/local/bin/chromedriver

# now, /usr/local/bin/chromedriver uses v83
# Selenium will always use whatever /usr/local/bin/chromedriver points to.
```

## Setup

### Virtual Environment
```bash
virtualenv -p python3.8 venv
. venv/bin/activate
python3.8 -m pip install -r requirements.txt
pytest -vvv
python3.8 run.py -h
```

### Docker Container
```bash
make image
make test
etc/run_in_container.sh -h
```
