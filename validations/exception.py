from flask import request, make_response
from functools import wraps

class RequestException(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def handle_request_exception(err):
    return make_response(err.error, err.status_code)

def accept_json(func):
    """
    Checks if the request to the route has 'application/json' or any
    value that accepts json in the accept header. If not, it will
    raise 406 HTTP error.    
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'application/json' not in request.accept_mimetypes:
            return make_response({
                "code": "not_acceptable",
                "description": "The accept header is missing or the media type does not support json."
            }, 406)
        return func(*args, **kwargs)
    return decorated
