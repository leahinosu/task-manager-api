from functools import wraps
from constants.constants import PAGE_LIMIT
from flask import request, make_response

def add_pagination(func):
    """
    Add next and prev url for get a collection requests.
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        res, offset = func(*args, **kwargs)
        prev_offset = offset - PAGE_LIMIT
        next_offset = offset + PAGE_LIMIT
        if prev_offset >= 0:
            prev = request.base_url + "?offset=" + str(prev_offset)
            res['prev'] = prev
        if next_offset < res['total']:
            next = request.base_url + "?offset=" + str(next_offset)
            res['next'] = next       
        return make_response(res, 200)
    return decorated