import json
from functools import wraps
from urllib.request import urlopen
from jose import jwt
from flask import request, session
from flask import make_response, _request_ctx_stack
import models.model as model
from config.config import Config

AUTH0_DOMAIN = Config.AUTH0_DOMAIN
API_AUDIENCE = Config.AUTH0_CLIENT_ID
ALLOWED_ENDPOINTS = Config.AUTH_ALLOWED_ENDPOINTS
ALGORITHMS = ["RS256"]

########################### BEGIN CITED CODE ################################
# The following code is not my own.                                         #
# SOURCE: https://auth0.com/docs/quickstart/backend/python/01-authorization #
# This code validates authorizatoin token given by the client and handles   #
#  any exceptions from the process. I added the required_auth to bypass     #
#  any AtuhError raises for any endpoints in ALLOWED_ENDPOINTS. Also, it    #
#  checks whether the given sub value is registerd in the datastore.        #
#############################################################################

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def handle_auth_error(err):  
    return make_response(err.error, err.status_code)

def requires_auth(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth:
            if request.endpoint in ALLOWED_ENDPOINTS:
                return func(*args, **kwargs)
            raise AuthError({"code": "authorization_header_missing",
                             "description": "Authorization header is expected"}, 401)
        # Authorization must be in the "Bearer Token" format.
        parts = auth.split()
        if parts[0].lower() != "bearer":
            if request.endpoint in ALLOWED_ENDPOINTS:
                return func(*args, **kwargs)
            raise AuthError({"code": "invalid_header",
                             "description": "Authorization header must be Bearer Token"}, 401)
        if len(parts) != 2:
            if request.endpoint in ALLOWED_ENDPOINTS:
                return func(*args, **kwargs)
            raise AuthError({"code": "invalid_header",
                             "description": "Authorization header must be Bearer Token"}, 401)        
        token = parts[1]
        jsonurl = urlopen("https://"+ AUTH0_DOMAIN + "/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except Exception:
            if request.endpoint in ALLOWED_ENDPOINTS:
                return func(*args, **kwargs)
            raise AuthError({"code": "invalid_header",
                             "description": "Unable to parse authentication token."}, 401)            
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer="https://" + AUTH0_DOMAIN + "/"
                )
            except jwt.ExpiredSignatureError:
                if request.endpoint in ALLOWED_ENDPOINTS:
                    return func(*args, **kwargs)
                raise AuthError({"code": "token_expired",
                                 "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                if request.endpoint in ALLOWED_ENDPOINTS:
                    return func(*args, **kwargs)
                raise AuthError({"code": "invalid_claims",
                                 "description": "incorrect claims, please check the audience and issuer"}, 401)
            except Exception:
                if request.endpoint in ALLOWED_ENDPOINTS:
                    return func(*args, **kwargs)
                raise AuthError({"code": "invalid_header",
                                 "description": "Unable to parse authentication token."}, 401)
            # Confrim the user_id is in datastore.
            if len(model.get_entity_by_name("users", payload['sub'])) != 1:
                if request.endpoint in ALLOWED_ENDPOINTS:
                    return func(*args, **kwargs)
                raise AuthError({"code": "invalid_user_id",
                                 "description": "The user id is not in datastore."}, 401)
            session['user_id'] = payload['sub']
            _request_ctx_stack.top.curernt_user = payload
            return func(*args, **kwargs)
        if request.endpoint in ALLOWED_ENDPOINTS:
            return func(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                         "description": "Unable to find appropriate key"}, 401)   
    return decorated

############################ END CITED CODE ################################