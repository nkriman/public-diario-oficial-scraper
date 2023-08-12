from .base_parser import BaseParser
from PyPDF2 import PdfReader
from io import BytesIO
from utils.helpers import retry_on_request


class PdfParser(BaseParser):
    @retry_on_request
    def get_pdf_text(self, pdf_link):
        # Download the file
        response = self.fetch_url(pdf_link)

        # Create a BytesIO object from the response content
        file = BytesIO(response.content)

        # Create a PDF reader instance
        pdf_reader = PdfReader(file)

        # Initialize an empty string to store the text
        text = ""

        # Iterate over all the pages and extract text
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            text += page.extract_text()

        return text
