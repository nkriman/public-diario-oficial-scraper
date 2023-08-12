import requests
from .proxy_rotation import get_gateway
from utils.helpers import retry_on_request

class BaseParser:
    @retry_on_request
    def fetch_url(self, url):
        try:
            gateway = get_gateway()  # Get the existing gateway instance
            session = requests.Session()
            session.mount(gateway.site, gateway)
            response = session.get(url)
            response.raise_for_status()  # Ensure we got a successful response
            return response
        except (ConnectionError, IOError) as e:
            raise e
