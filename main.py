import json
from database.db_connection import get_connection
from database.db_operations import upload_to_db
from scraper.base_scraper import BaseScraper
from scraper.diario_oficial_scraper import (
    DiarioOficialScraper,
    soup_to_dictionary,
    fetch_url,
    parse_html,
)
from parser.pdf_parser import PdfParser
from utils.helpers import clean_text, parse_json, get_dates_in_range, trim_text
from processor.openai_processor import (
    openai_setup,
    get_incorporation_entities,
    get_modification_entities,
    function_disolucion,
)
import uuid
import logging
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
import os
import time
import random
from parser.proxy_rotation import get_gateway, shutdown_gateway
from multiprocessing import Pool


logging.basicConfig(level=logging.INFO)

MIN_DELAY = 0.01
MAX_DELAY = 0.3

# Initialize apigateway for proxy rotation

base_url = "https://www.diariooficial.interior.gob.cl"
gateway = get_gateway(base_url)

load_dotenv()  # take environment variables from .env.
# establish db connection
logging.info("Establishing server connection")
engine = get_connection(
    user=os.getenv("AZURE_DB_USER"),
    password=os.getenv("AZURE_DB_PASSWORD"),
    host=os.getenv("AZURE_DB_HOST"),
)
# establish openai connection
logging.info("Establishing OpenAI connection")
openai_setup(secrets=os.getenv("API_KEY"))
# establish openai functions
functions = {
    "CONSTITUCIÓN": get_incorporation_entities,
    "MODIFICACIÓN": get_modification_entities,
    "DISOLUCIÓN": function_disolucion,
}


def main():
    # Unique batch id for this run
    batch_id = str(uuid.uuid4())  # create DiarioOficialScraper instance
    # Set date range (optional), Can be set to None, in which case it will default to only Today
    publication_date_range = get_dates_in_range("01-12-2017", "01-09-2018")
    with Pool() as p:
        p.starmap(
            process_date,
            [
                (
                    date,
                    functions,
                    os.getenv("AZURE_DB_USER"),
                    os.getenv("AZURE_DB_PASSWORD"),
                    os.getenv("AZURE_DB_HOST"),
                    batch_id,
                )
                for date in iter_dates(publication_date_range)
            ],
        )


def process_date(publication_date, functions, user, password, host, batch_id):
    # establish db connection
    engine = get_connection(user=user, password=password, host=host)

    diario_oficial = DiarioOficialScraper(publication_date)
    logging.info(f"Scraping for publication date: {diario_oficial.date}")
    editions = diario_oficial.fetch_editions()
    logging.info(f"Found {len(editions)} editions for {diario_oficial.date}")

    for edition in editions:
        process_edition(edition, functions, publication_date, engine, batch_id)

    # Create a generator that yields one date at a time


def iter_dates(dates):
    if dates is None:
        yield None
    else:
        for date in dates:
            yield date

      

def process_edition(edition, functions, publication_date, engine, batch_id):
    # Convert the edition URL to point to the "empresas_cooperativas" section
    url_parts = edition.split("?")
    specific_url = f"https://www.diariooficial.interior.gob.cl/edicionelectronica/empresas_cooperativas.php?{url_parts[1]}"
    # fetch url and parse html
    response = fetch_url(specific_url)
    soup = parse_html(response)
    # extract content and save it as a dictionary
    contents = soup_to_dictionary(soup)
    # iterate over the companies and their pdfs
    logging.info("Starting extraction...")
    for section, function in functions.items():
        if "Sumario" in contents and "Empresas y Cooperativas" in contents["Sumario"]:
            if section in contents["Sumario"]["Empresas y Cooperativas"]:
                for sub_section in contents["Sumario"]["Empresas y Cooperativas"][
                    section
                ][""]:
                    for item in contents["Sumario"]["Empresas y Cooperativas"][section][
                        ""
                    ][sub_section]:
                        pdf_link = item["link"]
                        # get the text content of the pdf
                        logging.info(f"Parsing PDF link: {pdf_link}")
                        time.sleep(
                            random.uniform(MIN_DELAY, MAX_DELAY)
                        )  # Be nice to the government
                        item["text_content"] = PdfParser().get_pdf_text(pdf_link)
                        item["clean_text_content"] = clean_text(item["text_content"])
                        item["trimmed_text_content"] = trim_text(
                            item["clean_text_content"]
                        )
                        item["section"] = section
                        item["sub_section"] = sub_section
                        item["publication_date"] = publication_date

                        logging.info("Uploading record to database")
                        upload_to_db(engine, item, batch_id)
            else:
                logging.info(f"No available content in section: {section}")
        else:
            logging.info("Reached end of file")


if __name__ == "__main__":
    main()
