from flask import Blueprint, request, make_response, session
import models.model as model
from validations.auth import requires_auth
from validations.exception import accept_json
from helper.pagination import add_pagination

task_api = Blueprint('task_api', __name__)

@task_api.post('/tasks')
@accept_json
@requires_auth
def task_post():
    """
    Add a task entity to datastore. Intialize 'owner', 'completed', and
    'task_list' porperties. Response contains the task properties and
    the datastore 'id' of the task and 'self' link of the task. It requires
    a valid authorization token.
    """
    task_property = request.get_json()
    task_property['owner'] = session['user_id']
    task_property['completed'] = False
    task_property['task_list'] = {}
    task = model.add_task(task_property)
    id = task.key.id
    task['id'] = id
    task['self'] = request.url + '/' + str(id)
    session.pop('user_id')
    return make_response(task, 201)

@task_api.get('/tasks')
@accept_json
@requires_auth
@add_pagination
def task_get():
    """
    Return a collection of tasks. If the authorization token is valid,
    it returns the owner's tasks. Otherwise, it will return an error message.

    'total' contains the total number of the tasks in datasotre.
    """
    offset = request.args.get('offset')
    if not offset: offset = 0
    else: offset = int(offset)
    user_id = session['user_id']
    tasks, total = model.get_tasks(offset, user_id)    
    for task in tasks:
        task['id'] = task.key.id
        task['self'] = request.base_url + '/' + str(task.key.id)
    res = {'tasks': tasks, 'total': total}
    session.pop('user_id')
    return res, offset

@task_api.get('/tasks/<int:task_id>')
@accept_json
@requires_auth
def task_get_by_id(task_id):
    """
    Return a task of the task_id. It requires a valid authorization token.
    """
    task = model.get_task_by_id(task_id, session['user_id'])
    task['id'] = task.key.id
    task['self'] = request.url
    session.pop('user_id')
    return make_response(task, 200)

@task_api.route('/tasks/<int:task_id>', methods=['PATCH', 'PUT'])
@accept_json
@requires_auth
def task_patch_put(task_id):
    """
    Update a task entity. It requires a valid authorization token, and
    only the owner can update the task. User can update the task properties
    stored in datastore except the 'task_list' and 'owner' properties.
    """
    task_property = request.get_json()
    user_id = session['user_id']
    task = model.update_task(task_id, task_property, user_id)
    task['id'] = task.key.id
    task['self'] = request.url
    session.pop('user_id')
    return make_response(task, 200)

@task_api.route('/tasks/<int:task_id>', methods=['DELETE'])
@requires_auth
def task_delete(task_id):
    """
    Delete a task entity. If it is in a task list, remove it from the list
    before deleted. Only the owner can perform this action.
    """
    user_id = session['user_id']
    model.delete_task(task_id, user_id)
    session.pop('user_id')
    return make_response('', 204)
