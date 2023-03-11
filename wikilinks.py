import sys
import logging
from logging import StreamHandler
from urllib.parse import unquote
from threading import Thread

import requests
from bs4 import BeautifulSoup

from exception import WikiLinksException
from settings import ERRORS, BASE_URL
from utils import validate_link, link_name, clean_paragraph, write_log, clear_log


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


class WikiLinks:
    def __init__(self, first_link, second_link):
        self.first_link = validate_link(first_link)
        self.second_link = validate_link(second_link)
        self.relation = {
            1: dict(),
            2: dict(),
            3: dict()
        }
        self.link_simple_tree = {
            1: dict(),
            2: dict(),
            3: dict()
        }

    @staticmethod
    def get_html_page(url_part: str, html_pages: list) -> str:
        """
        Sending request to Wikipedia page and returns html content. Appending html to list for workers
        :param url_part: url_part for sending request or writing it in relations dict
        :param html_pages: list of html pages from worker to parse later
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
    def parse_links(link_html: str) -> dict or str:
        """
        Returns links list from Wiki page html
        :param link_html: Wiki page html
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
        path = {
            'first': None or dict(),
            'second': None or dict(),
            'third': None or dict()
        }
        if level == 1:
            article_1 = self.link_simple_tree[1][found_link]

            path['first'] = {found_link: article_1}

        elif level == 2:
            article_2 = self.link_simple_tree[2][found_link]
            link_1 = self.relation[2][found_link]
            article_1 = self.link_simple_tree[1][link_1]

            path['second'] = {found_link: article_2}
            path['first'] = {link_1: article_1}

        elif level == 3:
            article_3 = self.link_simple_tree[3][found_link]
            link_2 = self.relation[3][found_link]
            article_2 = self.link_simple_tree[2][link_2]
            link_1 = self.relation[2][link_2]
            article_1 = self.link_simple_tree[1][link_1]

            path['third'] = {found_link: article_3}
            path['second'] = {link_2: article_2}
            path['first'] = {link_1: article_1}

        return path

    def search_path(self) -> dict or bool:
        """
        Method called from main part. Organising parsing and searching for goal link
        """
        first_link = self.first_link
        second_link = self.second_link

        level = 0
        link_heap = [first_link]
        logger.info('The search has begun!')

        while True:
            if level > 2:
                return False

            logger.info(f'Searching at depth {level + 1} ...')

            while link_heap:
                html_pages = []
                threads = []
                for i in range(100):
                    if link_heap:
                        t = Thread(target=self.get_html_page, args=(link_heap.pop(), html_pages))
                        threads.append(t)
                        t.start()
                for thread in threads:
                    thread.join()
                for html_page in html_pages:
                    parsed_links = self.parse_links(html_page[0])
                    for parsed_link, article in parsed_links.items():
                        write_log(parsed_link)
                        self.link_simple_tree[level + 1][parsed_link] = article
                        self.relation[level + 1][parsed_link] = html_page[1]
                        if parsed_link == second_link:
                            path = self.build_path(parsed_link, level + 1)
                            return path
            link_heap = []

            if not link_heap:
                level += 1
                for tree_link in self.link_simple_tree[level].keys():
                    link_heap.append(tree_link)


if __name__ == '__main__':
    clear_log()
    sample_one = 'https://ru.wikipedia.org/wiki/Xbox_360_S'
    sample_two = 'https://ru.wikipedia.org/wiki/Nintendo_3DS'

    try:
        first_url = str(validate_link(input('Write URL you want to start searching from '
                                            '(or tap Enter to go with example URL):')) or sample_one)
        first_name = link_name(first_url)
        write_log(validate_link(first_url))

        second_url = str(validate_link(input('Write URL you want to find '
                                             '(or tap Enter to go with example URL):')) or sample_two)
        second_name = link_name(second_url)

        wikilinks = WikiLinks(first_url, second_url)
        result = wikilinks.search_path()
        if result:
            logger.info(f'\n ------ Path from "{first_name}" to "{second_name}" ------ \n')
            for step in [result['first'], result['second'], result['third']]:
                if step:
                    for link, sent in step.items():
                        logger.info(f'\n{sent}')
                        logger.info(f'-> {BASE_URL + "/" + link} <-\n')
        else:
            logger.info('Path not found :(')
    except KeyboardInterrupt or WikiLinksException:
        logger.info('Ending...')
