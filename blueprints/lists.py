from flask import Blueprint, request, make_response, session
import models.model as model
from validations.auth import requires_auth
from validations.exception import accept_json
from helper.pagination import add_pagination


list_api = Blueprint('list_api', __name__)

@list_api.post('/lists')
@accept_json
@requires_auth
def list_post():
    """
    Add a task list entity to the datastore. Initialize 'owner' and
    'tasks' property of the task. Response contains 'id' of the datastore
    and 'self' link of the entity. Requires a valid authorization token.
    """
    
    task_list_property = request.get_json()  

    # Initializae owner and tasks
    task_list_property['owner'] = session['user_id']
    task_list_property['tasks'] = []

    task_list = model.add_task_list(task_list_property)
    id = task_list.key.id
    task_list['id'] = id
    task_list['self'] = request.url + '/' + str(id)
    session.pop('user_id')
    return make_response(task_list, 201)

@list_api.get('/lists')
@accept_json
@requires_auth
@add_pagination
def list_get():
    """
    Response contains a list of task list collections of the owner if the
    authorization token is valid. If the token is invalid, the response
    will contains any public task lists.

    'total' in the response is the total number of entities in the datastore.
    'lists' in the response will contain the number of task lists at most the
    PAGE_LIMIT number set in config.config.
    """
    offset = request.args.get('offset')
    if not offset: offset = 0
    else: offset = int(offset)
    user_id = session['user_id'] if 'user_id' in session else None
    task_lists, total = model.get_task_lists(offset, user_id)
    for task_list in task_lists:
        id = task_list.key.id
        task_list['id'] = id
        task_list['self'] = request.base_url + '/' + str(id)
    res = {'lists': task_lists, 'total': total}
    if 'user_id' in session: session.pop('user_id')
    return res, offset

@list_api.get('/lists/<int:list_id>')
@accept_json
@requires_auth
def list_get_by_id(list_id):
    """
    The response contain a data of a list of the list_id. If the list is 
    public, it will return even if the authorization token is invalid or
    the user is not the owner.
    """
    user_id = session['user_id'] if 'user_id' in session else None
    list = model.get_task_list_by_id(list_id, user_id)
    list['id'] = list.key.id
    list['self'] = request.url
    if 'user_id' in session: session.pop('user_id')
    return make_response(list, 200)

@list_api.route('/lists/<int:list_id>', methods=['PATCH', 'PUT'])
@accept_json
@requires_auth
def list_patch_put(list_id):
    """
    Update a list entity and return the updated one. If the request is
    PUT, it requires all required properties in the request.
    """
    task_list_property = request.get_json()
    user_id = session['user_id']
    task_list = model.update_task_list(list_id, task_list_property, user_id)
    task_list['id'] = task_list.key.id
    task_list['self'] = request.url
    session.pop('user_id')
    return make_response(task_list, 200)

@list_api.route('/lists/<int:list_id>', methods=['DELETE'])
@requires_auth
def list_delete(list_id):
    """
    Delete a list entity and its tasks.
    """
    user_id = session['user_id']
    model.delete_task_list(list_id, user_id)
    return make_response('', 204)

@list_api.route('/lists/<int:list_id>/tasks/<int:task_id>', methods=['PATCH'])
@requires_auth
def list_task_patch(list_id, task_id):
    """
    Add a task to a lists.
    
    Both the task and the list have to be owned by the user.
    If a task is already in a list, it cannot be added to the list.
    """
    user_id = session['user_id']
    task = model.get_task_by_id(task_id, user_id)
    task_list = model.get_task_list_by_id(list_id, user_id)
    # Check if task's task_list field is not empty.
    if task['task_list'] != {}:
        return make_response({
            "code": "task_list_not_empty",
            "description": "The task is already added to a list"
        }, 403)
    
    # Update task and list
    task_list['tasks'].append({
        'id': task_id,
        'name': task['name']
    })
    task["task_list"] = {
        'id': list_id,
        'name': task_list["name"]
    }       
    model.update_entity_rel(task)
    model.update_entity_rel(task_list)
    session.pop('user_id')
    return make_response('', 204)

@list_api.route('/lists/<int:list_id>/tasks/<int:task_id>', methods=['DELETE'])
@requires_auth
def list_task_delete(list_id, task_id):
    """
    Remove a task from a list.

    Both the task and the list have to be owned by the user.
    If the task isn't in any lists, it cannot be removed from the list.
    If the task is in a different list, it cannot be removed from the list.
    """
    user_id = session['user_id']
    task = model.get_task_by_id(task_id, user_id)
    task_list = model.get_task_list_by_id(list_id, user_id)
    # Check if task's task_list is empty.
    if task['task_list'] == {}:
        return make_response({
            "code": "task_list_empty",
            "description": "The task is not in any lists."
        }, 403)
    # Check if list_id is the same as the one from task's task_list.
    task_list_id = task['task_list']['id']
    if list_id != task_list_id:
        return make_response({
            "code": "list_id_not_matching",
            "description": "The task is not in the list."
        }, 403)

    # Update task and list
    for t in task_list["tasks"]:
        if t["id"] == task_id:
            task_list["tasks"].remove(t)
            break
    task["task_list"] = {}
    model.update_entity_rel(task)
    model.update_entity_rel(task_list)     
    return make_response('', 204)
        