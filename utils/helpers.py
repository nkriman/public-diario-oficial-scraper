from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import tiktoken
from .constants import MAX_TOKENS
import re
import openai.error
import requests
from sqlalchemy.exc import OperationalError
from datetime import datetime, timedelta
from requests.exceptions import ReadTimeout
import psycopg2


# Define a decorator for retrying failed requests
retry_on_request = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=5, max=15),
    retry=retry_if_exception_type(
        (
            openai.error.Timeout,
            openai.error.APIError,
            openai.error.APIConnectionError,
            openai.error.ServiceUnavailableError,
            requests.HTTPError,
            OperationalError,
            ConnectionError,
            ConnectionResetError,
            ReadTimeout,
            psycopg2.OperationalError,
            IOError,
        )
    ),
)


def clean_text(text):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    # Remove newline and extra spaces
    text = re.sub(r"\n", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(encoding.encode(text)) > MAX_TOKENS:
        text = text[:MAX_TOKENS]  # naive way

    return text


def parse_json(raw_json):
    # Replace single quotes with double quotes
    fixed_json_string = raw_json.replace("'", '"')

    # Remove comments
    fixed_json_string = re.sub(r"//.*?\n", "", fixed_json_string)

    # Remove trailing commas
    fixed_json_string = re.sub(r",\s*}", "}", fixed_json_string)
    fixed_json_string = re.sub(r",\s*]", "]", fixed_json_string)

    return fixed_json_string


def get_dates_in_range(from_date, to_date):
    if from_date is None or to_date is None:
        return None
    from_date = datetime.strptime(from_date, "%d-%m-%Y")
    to_date = datetime.strptime(to_date, "%d-%m-%Y")
    today = datetime.now()
    # Check if to_date is greater than from_date
    if to_date < from_date:
        raise ValueError(
            "Error: 'to_date' must be greater than or equal to 'from_date'."
        )
    # Check if to_date is not in the future
    if to_date > today:
        raise ValueError("Error: 'to_date' cannot be in the future.")
    delta = to_date - from_date
    date_list = [
        (from_date + timedelta(days=i)).strftime("%d-%m-%Y")
        for i in range(delta.days + 1)
    ]
    return date_list


def trim_text(text, search_word="EXTRACTO", search_range=800):
    """Function printing python version."""

    search_text = text[:search_range]

    try:
        start = search_text.index(search_word)
        return text[start:]
    except ValueError:
        print(
            f"'{search_word}' not found in the first {search_range} characters of the text."
        )
        return text
