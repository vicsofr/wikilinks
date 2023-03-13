import sys
import logging
from logging import StreamHandler
from urllib.parse import unquote
from threading import Thread

import requests
from bs4 import BeautifulSoup

from exception import WikiLinksException
from settings import ERRORS, BASE_URL, MAX_DEPTH
from utils import validate_link, link_name, clean_paragraph, write_log, clear_log


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


class WikiLinks:
    def __init__(self, first_link, second_link):
        self.first_link = first_link
        self.second_link = second_link
        self.simple_cache = set()
        self.relation = dict()
        self.link_simple_tree = dict()

    @staticmethod
    def get_html_page(url_part: str, html_pages: list) -> str:
        """
        Sending request to Wikipedia page and returns html content. Appending html to list for workers
        :param url_part: url_part for sending request or writing it in relations dict
        :param html_pages: list of html pages from worker to parse later
        :return: page html-content
        """
        related_link = url_part
        url = f'{BASE_URL}/{url_part}'

        response = requests.get(url)

        if response.status_code != 200:
            raise WikiLinksException(ERRORS['connection'] + ' ' + url)

        html_content = response.content.decode('utf-8')
        html_pages.append((html_content, related_link))
        return html_content

    @staticmethod
    def parse_links(link_html: str) -> dict:
        """
        Parsing received html-content and returning link with a sentence where it was found
        :param link_html: Wiki page html
        :return: dict() where parsed link is a key and sentence is a value
        """
        parsed_links = dict()

        soup = BeautifulSoup(link_html, 'html.parser')
        p_tags = soup.find_all('p')
        for p_tag in p_tags:
            cleaned_p = clean_paragraph(p_tag)
            a_tags = p_tag.find_all('a')
            if a_tags:
                for a_tag in a_tags:
                    if a_tag.has_attr('href') and a_tag['href'][:6] == '/wiki/':
                        clean_link = unquote(a_tag['href'][6:])
                        parsed_links[clean_link] = cleaned_p
        return parsed_links

    def build_path(self, found_link: str, level: int) -> dict:
        """
        Building path as a dict of three depth levels from link simple tree and relations dict.
        Key is a link, value is a sentence where the key was parsed
        :param found_link: goal link found in search function
        :param level: level at which the goal link was found
        :return: dict with a path to the goal link
        """
        path = dict()
        prev_link = found_link
        levels = list(range(1, level + 1))[::-1]
        for iteration, lvl in enumerate(levels, start=1):
            if iteration == 1:
                found_sentence = self.link_simple_tree[lvl][found_link]
                path[lvl] = {found_link: found_sentence}
            else:
                related_link = self.relation[lvl + 1][prev_link]
                found_sentence = self.link_simple_tree[lvl][related_link]
                prev_link = related_link
                path[lvl] = {related_link: found_sentence}
        return path

    def search_path(self, depth: int = 3) -> dict or bool:
        """
        Method called from __main__ part. Organising parsing and searching for goal link.
        :param depth: max searching depth, default = 3
        :return: path to goal link or False
        """
        first_link = self.first_link
        second_link = self.second_link
        restrict_depth = depth - 1

        cache = self.simple_cache
        link_simple_tree = self.link_simple_tree
        relations = self.relation

        level = 0
        link_heap = [first_link]
        logger.info('\n* The search has begun! *')

        while True:
            if level > restrict_depth:
                return False

            logger.info(f'- Searching at depth {level + 1} ...')

            while link_heap:
                html_pages = []
                threads = []
                for i in range(100):
                    if link_heap:
                        current_link = link_heap.pop()
                        t = Thread(target=self.get_html_page, args=(current_link, html_pages))
                        cache.add(current_link)
                        write_log(current_link)
                        threads.append(t)
                        t.start()
                for thread in threads:
                    thread.join()
                for html_page in html_pages:
                    parsed_links = self.parse_links(html_page[0])

                    for parsed_link, article in parsed_links.items():
                        try:
                            link_simple_tree[level + 1]
                        except KeyError:
                            link_simple_tree[level + 1] = dict()
                        try:
                            relations[level + 1]
                        except KeyError:
                            relations[level + 1] = dict()
                        link_simple_tree[level + 1][parsed_link] = article
                        relations[level + 1][parsed_link] = html_page[1]

                        if parsed_link == second_link:
                            path = self.build_path(parsed_link, level + 1)
                            return path

            link_heap = []

            if not link_heap:
                level += 1
                for tree_link in link_simple_tree[level].keys():
                    if tree_link not in cache:
                        link_heap.append(tree_link)


if __name__ == '__main__':
    from settings import MAX_DEPTH
    clear_log()
    sample_one = 'https://ru.wikipedia.org/wiki/Xbox_360_S'
    sample_two = 'https://ru.wikipedia.org/wiki/Nintendo_3DS'

    try:
        first_url = validate_link(str(input('\n-> Write URL you want to start searching from '
                                            '(or tap Enter for example URL): ') or sample_one))
        first_name = link_name(first_url)

        second_url = validate_link(str(input('-> Write URL you want to find '
                                             '(or tap Enter for example URL): ')) or sample_two)
        second_name = link_name(second_url)

        max_depth = int(input('-> Type searching depth (or tap Enter for settings depth value): ') or str(MAX_DEPTH))

        wikilinks = WikiLinks(first_url, second_url)
        result = wikilinks.search_path(depth=max_depth)

        if result:
            logger.info(f'\n ------ Path from "{first_name}" to "{second_name}" ------ \n')
            for step in range(1, max_depth):
                try:
                    for link, sentence in result[step].items():
                        logger.info(f'\n{sentence}')
                        logger.info(f'-> {BASE_URL + "/" + link} <-\n')
                except KeyError:
                    pass
        else:
            logger.info('Path not found :(')
    except KeyboardInterrupt or WikiLinksException:
        logger.info('\nEnding...')
