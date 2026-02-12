import hashlib
from datetime import datetime
import os

# TODO: current implementation is closer to a pepper
SALT = os.getenv('SALT')

"""adapted from https://github.com/HermanMartinus/bearblog/blob/master/blogs/helpers.py#L121"""
def salt_and_hash(request, duration='day'):
    ip = client_ip(request)
    if duration == 'year':
        ip_date_salt_string = f"{ip}-{datetime.now().year}-{SALT}"
    else:
        ip_date_salt_string = f"{ip}-{datetime.now().date()}-{SALT}"

    hash_id = hashlib.sha256(
        ip_date_salt_string.encode('utf-8')
    ).digest()
    return hash_id

def client_ip(request):
    return request.remote_addr