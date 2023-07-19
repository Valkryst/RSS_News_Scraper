import fcntl
import logging
import os
import pickle
import random
import time
import traceback
from datetime import datetime
from random import randint

import feedparser
from newspaper import Article

DATA_FOLDER = 'data'
ARTICLES_FOLDER = os.path.join(DATA_FOLDER, 'articles')

LOCK_FILE = 'lockfile.lock'
LOG_FILE = 'logs.txt'
SCRAPED_URLS_CACHE_FILE = os.path.join(DATA_FOLDER, 'scraped_urls_cache.pkl')
RSS_URLS_FILE = 'rss_urls.txt'


def create_required_files_and_folders():
    """
    Create required files and directories if they do not already exist.

    :return: None
    """

    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ARTICLES_FOLDER, exist_ok=True)

    if not os.path.exists(RSS_URLS_FILE):
        open(RSS_URLS_FILE, 'a').close()


def get_logger():
    logger = logging.getLogger()
    log_level = os.getenv('LOG_LEVEL', 'WARNING')

    # Map from string level to logging level
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }

    logger.setLevel(level_map.get(log_level, logging.WARNING))

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create console handler, set level of logging and add formatter
    ch = logging.StreamHandler()
    ch.setLevel(logger.level)
    ch.setFormatter(formatter)

    # Create file handler, set level of logging and add formatter
    fh = logging.FileHandler(LOG_FILE)
    fh.setLevel(logger.level)
    fh.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger


def load_rss_feeds():
    """
    Load the RSS URLs from a file.

    :return: List of RSS URLs.
    """

    with open(RSS_URLS_FILE, 'r') as file:
        return [line.strip() for line in file]


def load_scraped_urls_cache():
    """
    Load the cache file or create a new one if it doesn't exist.

    :return: Set of scraped URLs.
    """

    if not os.path.exists(SCRAPED_URLS_CACHE_FILE):
        return set()

    with open(SCRAPED_URLS_CACHE_FILE, 'rb') as file:
        return pickle.load(file)


def save_scraped_urls_cache(scraped_urls):
    """
    Save the set of scraped URLs to a cache file.

    :param scraped_urls: Set of scraped URLs.
    :return: None
    """

    if len(scraped_urls) == 0:
        return

    with open(SCRAPED_URLS_CACHE_FILE, 'wb') as file:
        pickle.dump(scraped_urls, file)


def get_new_rss_entries(scraped_urls):
    """
    Get new URLs from the RSS feeds.

    :param scraped_urls: Set of scraped URLs.
    :return: Set of new URLs.
    """

    unseen_entries = []

    for feed in load_rss_feeds():
        for entry in feedparser.parse(feed).entries:
            if entry.link not in scraped_urls:
                unseen_entries.append(entry)

    return unseen_entries


def download_article(entry):
    """
    Attempt to download and parse an article from a URL.

    :param entry: Entry containing the URL of the article to download.
    :return: Parsed article data.
    """

    article = Article(entry.link)
    article.download()
    article.parse()

    published_at = datetime.utcnow()
    published_at = article.publish_date if article.publish_date else published_at
    published_at = datetime(*entry.published_parsed[:6]) if entry.published_parsed else published_at

    return {
        'url': entry.link,
        'title': article.title,
        'body': article.text,
        'published_at': published_at
    }


def save_articles_to_disk(articles):
    """
    Save the articles to disk.

    :param articles: List of articles to save.
    :return: None
    """

    os.makedirs(ARTICLES_FOLDER, exist_ok=True)

    for article in articles:
        # We save space by removing the publication date from the article and using it in file name.
        publish_date = article['published_at'].date()
        article.pop('published_at')

        file_path = os.path.join(ARTICLES_FOLDER, f'{publish_date}.pkl')

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                existing_data = pickle.load(f)
                existing_data.append(article)
        else:
            existing_data = [article]

        with open(file_path, 'wb') as f:
            pickle.dump(existing_data, f)


def main():
    create_required_files_and_folders()

    logger = get_logger()
    lockfile = open(LOCK_FILE, 'w+')

    try:
        try:
            fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            logger.error('Another instance of this program is already running.')
            exit(1)

        scraped_urls = load_scraped_urls_cache()
        entries = get_new_rss_entries(scraped_urls)
        random.shuffle(entries)  # We shuffle the entries to avoid being blocked by the server for making too many requests.

        articles = []

        for entry in entries:
            time.sleep(randint(5, 15))

            try:
                logger.info(f'Downloading article from {entry.link}.')
                article = download_article(entry)

                if article:
                    articles.append(article)
                    logger.info(f'Article downloaded successfully.')
                    scraped_urls.add(entry.link)
                else:
                    logger.warning(f"Failed to download article from {entry.link}")

            except Exception as e:
                logger.error(f"Error downloading article from {entry.link}: {e}")
                logger.error(traceback.format_exc())
                continue

        save_scraped_urls_cache(scraped_urls)
        logger.info('Updated scraped URLs cache.')

        save_articles_to_disk(articles)
        logger.info('Updated article data files.')
    finally:
        fcntl.flock(lockfile, fcntl.LOCK_UN)
        lockfile.close()
        os.remove(LOCK_FILE)

        logger.info('Finished scraping RSS feeds.')


if __name__ == '__main__':
    main()
