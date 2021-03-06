""" Morgue Spider

      / _ \
    \_\(_)/_/
     _//"\\_
      /   \

This script spiders DCSS websites looking for morgue files.

PLEASE BE CAREFUL.

The people who run DCSS websites do so at their own personal cost.
They do not have the resources of a billion-dollar company, and you CAN cost significant
problems for them by bogging down their servers were tons of spider requests.

The absolute MINIMUM wait time you should use between spider requests is 1 minute. This is the
industry standard spider wait time used by Google.  But Google isn't trying to be a good citizen.
The longer the wait you put on this spider script, the nicer you will be to the people that
volunteer their time to run DCSS's non-profit websites.

Please consider setting WAIT_SECONDS to 120. or longer, and never run this script in parallel.
"""
from bs4 import BeautifulSoup
from bz2 import BZ2File
from datetime import datetime
from glob import glob
import os
from random import random
from requests import get as get_url
from sys import argv
from library_data import *
from known_morgues import KnownMorgues
from url_iterator import URLIterator

# CONSTANTS
AUTO_SAVE_SECONDS = 30 * 60
SEARCH_DEPTH = 3
STARTING_URL_FILE = 'data/starting_urls.txt'


def main():
    # grab global config varaibles
    auto_save = int(AUTO_SAVE_SECONDS)
    depth = int(SEARCH_DEPTH)
    starting_url_file = STARTING_URL_FILE

    # optional commandline parsing
    a = 1
    while a < len(argv):
        if argv[a].lower() in ('-a', '--auto_save_second'):
            a += 1
            auto_save = int(argv[a])
        elif argv[a].lower() in ('-d', '--depth'):
            a += 1
            depth = int(argv[a])
        elif argv[a].lower() in ('-u', '--url_file'):
            a += 1
            starting_url_file = argv[a]
        a += 1

    # parse input file for starting URLS
    starting_urls = [u.strip() for u in open(starting_url_file, 'r').readlines()]

    # run spider
    ms = MorgueSpider(starting_urls, auto_save, depth)
    all_urls = ms.spider()
    print('Spidered {0} URLs'.format(len(all_urls)))


class MorgueSpider:

    def __init__(self, urls, auto_save=1800, depth=3):
        self.urls = urls
        self.auto_save = float(auto_save)
        self.depth = int(depth)
        self.data_dir = DATA_DIR
        self.dt_fmt = DT_FMT
        self.losers = LOSERS
        self.morgue_urls = MORGUE_URLS
        self.parser_errors = PARSER_ERRORS
        self.winners = WINNERS

    def spider(self):
        """ Spider through all the links you can find, recursively, to look for DCSS morgue files,
        write all those you find to a simple text file

        Args:
            depth (int): Number of links to follow down into, spidering depth
        Returns:
            set: All the URLs that were found during the spidering
        """
        return self._spider(set(self.urls), set(self.urls), self.depth)

    def _spider(self, all_urls, new_urls, depth):
        """ Spider through all the links you can find, recursively, to look for DCSS morgue files,
        write all those you find to a simple text file

        Args:
            all_urls (set): URLs we have alreay spidered
            new_urls (set): URLs we have yet to spider
            depth (int): Number of links to follow down into, spidering depth
        Returns:
            set: All the URLs that were found during the spidering
        """
        if depth <= 0 or len(new_urls) == 0:
            return all_urls

        print('Depth {0}: {1} new URLs'.format(depth, len(new_urls)))
        print('\t', end='', flush=True)

        # init some loop variables
        start = datetime.now().timestamp()
        newer_urls = set()

        url_iter = URLIterator(new_urls)
        for url in url_iter:
            if not (url.endswith('.html') and self._looks_crawl_related(url)):
                # let's not spider the whole internet
                continue

            # look for links inside this URL
            print('.', end='', flush=True)
            newer_urls.update(MorgueSpider.find_links_in_file(url))

            # write a temp output file if it's been too long
            if datetime.now().timestamp() - start > self.auto_save:
                self._write_morgue_urls_to_file(newer_urls - all_urls)
                start = datetime.now().timestamp()
                print('\t', end='', flush=True)

        # write any new morgues you found to file
        newer_urls = newer_urls - all_urls
        self._write_morgue_urls_to_file(newer_urls)

        return self._spider(all_urls.union(newer_urls), newer_urls, depth - 1)

    @staticmethod
    def _looks_crawl_related(url):
        """ Determine if, broadly, it seems likely a URL is DCSS-related.

        Args:
            url (str): Any arbitary URL
        Returns:
            bool: Could this URL possibly be a DCSS link?
        """
        u = url.lower()
        crawl_terms = ('crawl', 'dcss', 'morgue')

        for term in crawl_terms:
            if term in u:
                return True

        return False

    @staticmethod
    def find_links_in_file(url):
        """ Find all the HTML links we can on a given webpage.

        Args:
            url (str): Any arbitary URL
        Returns:
            set: All the URLs we could find on that page.
        """
        r = get_url(url)
        html = r.content
        soup = BeautifulSoup(html, features="html.parser")
        all_links = soup.findAll('a')
        return set([a['href'].strip() for a in all_links])

    def _write_morgue_urls_to_file(self, urls):
        """ Write all the morgues you found to a simple text file,
        checking to make sure you haven't found it before

        Args:
            urls (set): Lots of arbitrary morgue URLs
        Returns: None
        """
        # What morgue files have we already seen?
        known_morgues = KnownMorgues([self.morgue_urls, self.winners, self.losers, self.parser_errors], [self.data_dir])
        known_morgues.find()

        # Strip out known morgues.
        urls = [u for u in urls if not known_morgues.includes(u)]

        # only write valid links to file
        urls = [u for u in urls if u.startswith('http')]

        if not len(urls):
            print("\n\tFound no new morgues.")
            return
        else:
            print("\n\tWriting {0} new morgues to file.".format(len(urls)))

        # write all the new and unique morgues we have found to a text file
        file_path = os.path.join(self.data_dir, '{0}{1}.txt'.format(self.morgue_urls, datetime.now().strftime(self.dt_fmt)))
        with open(file_path, 'a+') as f:
            for url in sorted(urls):
                f.write(url)
                f.write('\n')

    @staticmethod
    def find_morgues(urls):
        """ Find the subset of URLs that look like they might be morgue files.

        Args:
            urls (set): A bunch of URLs
        Returns:
            list: All URLs that might be morgue files
        """
        return [u for u in urls if u.split('/')[-1].startswith('morgue') and u.endswith('.txt')]


if __name__ == '__main__':
    main()
