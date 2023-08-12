from .base_scraper import BaseScraper
from datetime import datetime
from utils.helpers import retry_on_request
from bs4 import BeautifulSoup
import requests


class DiarioOficialScraper(BaseScraper):
    def __init__(self, date=None):
        super().__init__()
        self.date = date if date else datetime.now().strftime("%d-%m-%Y")
        self.url = f"https://www.diariooficial.interior.gob.cl/edicionelectronica/index.php?date={self.date}"

    def fetch_editions(self):
        response = self.fetch_url(self.url)
        soup = self.parse_html(response)

        # Check if the page has a "No existen publicaciones" message
        if soup.find("p", class_="nofound"):
            print(f"No publications on {self.url}")
            return []
        else:
            # If there are multiple editions, find the hrefs
            if "select_edition" in response.url:
                edition_links = [
                    link.get("href")
                    for link in soup.find_all("a")
                    if "edition=" in link.get("href", "")
                ]
                # Append the base url to these hrefs
                edition_links = [
                    "https://www.diariooficial.interior.gob.cl/edicionelectronica/"
                    + link
                    for link in edition_links
                ]
            else:
                # If there's just one edition, get its URL
                edition_links = [response.url]

            return edition_links


def soup_to_dictionary(soup):
    soup_dictionary = {}  # Dictionary to store the soup_dictionary

    # Temporary variables to store the current titles
    title1 = title2 = title3 = title4 = title5 = None

    for row in soup.select("tr"):
        if "title1" in row.td.get("class", []):
            title1 = row.td.get_text(strip=True)
            soup_dictionary[title1] = {}
            title2 = title3 = title4 = title5 = None
        elif "title2" in row.td.get("class", []):
            title2 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2] = {}
            title3 = title4 = title5 = None
        elif "title3" in row.td.get("class", []):
            title3 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3] = {}
            title4 = title5 = None
        elif "title4" in row.td.get("class", []):
            title4 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3][title4] = {}
            title5 = None
        elif "title5" in row.td.get("class", []):
            title5 = row.td.get_text(strip=True)
            soup_dictionary[title1][title2][title3].setdefault(title4, {})[title5] = []
        elif "content" in row.get("class", []):
            name_div = row.select_one('td > div[style="float:left; width:550px;"]')
            rut_div = row.select_one('td > div[style="float:right;"]')
            link_a = row.select_one("td > a")
            if name_div and link_a:
                company_info = {
                    "company": name_div.text.strip(),
                    "link": link_a["href"],
                    "link_text": link_a.get_text(strip=True),
                }
                if rut_div:
                    company_info["RUT"] = rut_div.text.strip()
                soup_dictionary[title1][title2][title3].get(title4, {}).get(
                    title5, []
                ).append(company_info)

    return soup_dictionary


@retry_on_request
def fetch_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Ensure we got a successful response
    return response


def parse_html(response):
    soup = BeautifulSoup(response.content, "html.parser")
    return soup
