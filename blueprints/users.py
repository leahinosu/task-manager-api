from flask import Blueprint, request, make_response
import models.model as model
from validations.exception import accept_json


user_api = Blueprint('user_api', __name__)

@user_api.get('/users')
@accept_json
def user_get():
    """
    Returns all the users from datastore.
    """
    users =  model.get_users()
    for user in users:
        user['id'] = user.key.id
        user['self'] = request.url + '/' + str(user.key.id)    
    return make_response({
        'total': len(users),
        'users': users
    }, 200)

@user_api.get('/users/<int:user_id>')
@accept_json
def user_get_by_id(user_id):
    """
    Returns a user by the user_id. 
    """
    user = model.get_entity_by_id("users", user_id)
    return make_response(user, 200)