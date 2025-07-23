'''
Ever so often, the sanctus library website is being scanned for discount codes. This is shown to lite version users. Nothing happens here for other users.
'''

from . import auto_load as al
from .auto_load.common import *
from . import dev_info
from . import constants

CODES: OrNone[list[tuple[str, int]]] = None

def has_codes():
    if CODES is None:
        return False
    return len(CODES) > 0

@al.register_timer(first_interval=2, threaded=True, thread_delay=3600)
def update_discount_codes():
    if not dev_info.LITE_VERSION:
        return
    import requests
    global CODES
    try:
        response = requests.get(constants.DISCOUNT_LINK)
        text = response.text
        text = text.replace('\t', '')
        lines = text.split('\n')
        codes: list[tuple[str, int]] = []
        for l in lines:
            if l == '':
                continue
            if l.isspace():
                continue
            parts = l.split(' ')
            codes.append((parts[0], int(parts[1])))
        CODES = codes

    except requests.exceptions.RequestException:
        CODES = None
    return 10
