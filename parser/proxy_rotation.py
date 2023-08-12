from requests_ip_rotator import ApiGateway
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

_gateway = None

def get_gateway(base_url=None):
    global _gateway
    if _gateway is None:
        _gateway = ApiGateway(base_url)
        _gateway.start()
    return _gateway

def shutdown_gateway():
    global _gateway
    if _gateway is not None:
        _gateway.shutdown()
        _gateway = None