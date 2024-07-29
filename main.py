import json
from flask import Flask, session
from flask import  redirect, render_template, url_for, make_response
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
from blueprints.tasks import task_api
from blueprints.lists import list_api
from blueprints.users import user_api
from validations.request import BadRequest, handle_bad_request
from validations.exception import RequestException, handle_request_exception
from validations.auth import AuthError, handle_auth_error
from models.model import add_user
from config.config import Config


app = Flask(__name__)
app.secret_key = Config.APP_SECRET_KEY
app.register_blueprint(task_api)
app.register_blueprint(list_api)
app.register_blueprint(user_api)
app.register_error_handler(BadRequest, handle_bad_request)
app.register_error_handler(RequestException, handle_request_exception)
app.register_error_handler(AuthError, handle_auth_error)

#############################################################################
# General HTTP error handlers                                               #
#############################################################################
@app.errorhandler(404)
def page_not_found(err):
    return make_response({
        "code": "page_not_found",
        "description": "the page is not found."
    }, 404)
      
@app.errorhandler(405)
def method_not_allowed(err):
    return make_response({
        "code": "method_not_allowed",
        "description": "This endpoint does not support the request method."
    }, 405)

@app.errorhandler(415)
def unsupported_media_type(err):
    return make_response({
        "code": "unsupported_media_type",
        "description": "The content-type is not json."
    }, 415)


#############################################################################
# Register/Login/Logout pages for JWT                                       #
#############################################################################

########################### BEGIN CITED CODE ###############################
# The following code is not my own.                                        #
# SOURCE: https://auth0.com/docs/quickstart/webapp/python                  #
# This code adds login and logoff features to the app. If a user logged in #
#  it displays user's JWK to the main page. I added the feature to copy    #
#  id_token and sub (user_id) values to the clipboard.                     #
#  Updated 6/6/23 - new user's user name and user id is added to the       #
#    datastore.                                                            #
############################################################################

oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=Config.AUTH0_CLIENT_ID,
    client_secret=Config.AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{Config.AUTH0_DOMAIN}/.well-known/openid-configuration'
)

@app.route('/')
def index():
    return render_template("index.html", session=session.get('user'),
                           pretty=json.dumps(session.get('user'), indent=4))

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri = url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    user_id = token["userinfo"]["sub"]
    name = token["userinfo"]["name"]
    user_info = {
        'user_id': user_id,
        'name': name
    }
    add_user(user_info)  # Add the user to datastore
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + Config.AUTH0_DOMAIN
        + "/v2/logout?"
        + urlencode(
          {
              "returnTo": url_for("index", _external=True),
              "client_id": Config.AUTH0_CLIENT_ID,
          },
          quote_via = quote_plus,
        )
    )

############################ END CITED CODE ################################
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
