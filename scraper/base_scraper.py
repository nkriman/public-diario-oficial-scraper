from bs4 import BeautifulSoup
import requests
from utils.helpers import retry_on_request


class BaseScraper:
    def __init__(self):
        pass

    @retry_on_request
    def fetch_url(self, url):
        response = requests.get(url)
        response.raise_for_status()  # Ensure we got a successful response
        return response

    def parse_html(self, response):
        soup = BeautifulSoup(response.content, "html.parser")
        return soup


def parse_html(response):
    soup = BeautifulSoup(response.content, "html.parser")
    return soup
