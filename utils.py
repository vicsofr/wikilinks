import re
from datetime import datetime
from urllib.parse import unquote

from bs4 import BeautifulSoup

from settings import ERRORS, BASE_URL
from exception import WikiLinksException


def link_name(link: str) -> str:
    """
    Converts link from url to short name
    """
    split_link = link.split('/')
    normal_name = ' '.join(split_link[-1].split('_'))
    return normal_name


def clean_paragraph(paragraph: BeautifulSoup) -> str:
    """
    Cleaning BeautifulSoup's object text from unnecessary stuff
    """
    cleaned = re.sub(r'\[(.*?\d)\]', '', paragraph.getText(strip=False).replace("\xa0", " "))
    return cleaned


def validate_link(link: str) -> str:
    """
    Validates input link if URL belongs to Wikipedia pages. Only Russian segment for now
    :param link: full or short URL
    :return: validated URL
    """
    split_link = link.split('/')
    try:
        main_domain = '.'.join(split_link[2].split('.')[1:])
        language = split_link[2].split('.')[0]
        if split_link[0] != 'https:' or main_domain != 'wikipedia.org':
            raise WikiLinksException(ERRORS['wrong_url'])
        elif language != 'ru':
            raise WikiLinksException(ERRORS['wrong_lang'])
        elif split_link[3] != 'wiki':
            raise WikiLinksException(ERRORS['not_wiki'])
        else:
            result_link = split_link[-1]
            if result_link[0] == '%':
                return unquote(result_link)
            return result_link
    except IndexError:
        return link


def write_log(log_link):
    with open('entry_log.txt', 'a+') as file:
        file.write(f'[{datetime.now()}] {BASE_URL}/{log_link}\n')


def clear_log():
    path = 'entry_log.txt'
    try:
        open(path, 'w').close()
    except FileNotFoundError:
        pass
