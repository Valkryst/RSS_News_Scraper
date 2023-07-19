This script can be used to build a local database of news articles by crawling RSS feeds and downloading the articles.

* It can be run periodically (e.g. VIA [cron](https://en.wikipedia.org/wiki/Cron)) to keep the database up to date.
* It stores the articles in a local folder, in a simple format that can be easily loaded into memory.
* It does not allow multiple instances to run at the same time.
* It employs a cache to avoid downloading the same articles multiple times.
* It uses simple methods to avoid being blacklisted by websites, though no guarantees are made.

## Usage

1. Download `main.py` into a folder. Preferably, create a new folder for this purpose.
2. Install the required packages by running `pip install -r requirements.txt`.
3. Create a `rss_urls.txt` file and enter the RSS feed URLs you want to crawl. Each URL should be on a new line.
4. Run `python main.py` to start the crawler, or create a cron job to run it periodically.

## Output

The crawler will create a `data` folder and store the crawled data in it. Articles are grouped by publication date and stored in files named `YYYY-MM-DD.pkl`.

The `.pkl` files can be loaded as follows:

```python
import os
import pickle

articles = {}

for file in os.listdir('data/articles'):
    with open(os.path.join('data/articles', file), 'rb') as f:
        articles[file.replace('.pkl', '')] = pickle.load(f)
```

Each entry in the `articles` dict uses the following format:

```python
'YYYY-MM-DD': [
    {
        'url': 'example.com/articles/1',
        'title': 'Lorem ipsum dolor sit amet',
        'body': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    },
    {
        'url': 'example.com/articles/2',
        'title': 'Lorem ipsum dolor sit amet',
        'body': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    }
    # ...
]
```

## Logging

You can control the logging level by setting the `LOG_LEVEL` environment variable. The default level is `WARNING` and the list of levels can be found [here](https://docs.python.org/3/howto/logging.html).