import string
import random
import re
from urllib.parse import urlparse

def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def validate_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_short_code(code: str) -> bool:
    pattern = r'^[a-zA-Z0-9]{4,20}$'
    return bool(re.match(pattern, code))
