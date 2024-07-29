from google.cloud import datastore
from flask import request
from validations.request import validate_required, validate_task_property
from validations.request import validate_task_list_property
from validations.exception import RequestException
from constants.constants import PAGE_LIMIT
from constants.constants import TASK_REQUIRED_PROPERTIES
from constants.constants import LIST_REQUIRED_PROPERTIES


client = datastore.Client()

##############################################################################
# Add Entity                                                                 #
##############################################################################

def add_entity(kind, entity_info):
    """
    Add an entity to datastore.

    Parameters:
        kind : str
            the kind of an entity.
        entity_info : dict
            key-value pairs of the entity's properties.

    Returns:
        entity : google.datastore.Entity
            a datastore Entity object contains datastore key and properties
            of an entity.
    """
    entity = datastore.Entity(client.key(kind))
    entity.update(entity_info)
    client.put(entity)
    return entity

def add_task(task_property):
    """
    Add a task entity to datastore.

    Parameters:
        task_peorperty : dict
            key-value pairs of the task's properties
    """
    validate_required("tasks", task_property)
    validate_task_property(task_property)
    return add_entity("tasks", task_property)

def add_task_list(task_list_property):
    """
    Add a task list entity to datastore.
    It also checks whether the task_list's name is unique in the datstore.

    Parameters:
        task_list_property : dict
            key-value paris of the task_list's properties
    """
    validate_required("lists", task_list_property)
    validate_task_list_property(task_list_property)

    # Check duplicate name
    name = task_list_property["name"]
    user_id = task_list_property["owner"]
    result = get_list_same_name(name, user_id)
    if len(result) > 0:
        raise RequestException({
            "code": "list_name_not_unique",
            "description": "You already have a list with the same name."
        }, 403)

    return add_entity("lists", task_list_property)

def add_user(user_info):
    """
    Add a user entity to datastore.
    If the user id is already in the datstore, it won't add it.

    Parameters:
        user_info : dict
            key-value pairs of the user's properties.
    """
    user_id = user_info["user_id"]
    # Check if the user_id already in datastore.
    query = client.query(kind="users")
    query = list(query.add_filter("user_id", "=", user_id).fetch())
    if len(query) == 0:
        add_entity("users", user_info)


##############################################################################
# Get an Entity                                                              #
##############################################################################

def get_entity_by_name(kind, name):
    """
    Get an entity from datastore by the name property.
    If there isn't a matching name exists on the datstore, it will return None.

    Parameters:
        kind : str
            the kind of an entity
        name : str
            the name property of an entity
    
    Returns:
        query : list
            a list contains entities has the matching name.
    """
    query = client.query(kind=kind)
    query = query.add_filter('user_id', '=', name).fetch()
    return list(query)

def get_list_same_name(name, user_id):
    """
    Get an entity from datastore by the name property, and filter again
    by the given user_id. This is for add/edit list to check whether the
    name is unique.

    Parameters:
        user_id : str
            user's id of the App. 'sub' value of JWT
        name : str
            the name property of an entity
    
    Returns:
        query : list
            a list contains entities has the matching name and user id.
    """
    query = client.query(kind="lists")
    query = query.add_filter('name', '=', name)
    query = query.add_filter('owner', '=', user_id)
    return list(query.fetch())

def get_entity_by_id(kind, id):
    """
    Return an entity from datastore by the datastore id.
    If there is not an entity of the such id, it will raise RequestException.

    Parameters
        kind : str
            the 'kind' key of datastore
        id : int
            the datastore id of the entity.
    Returns
        entity : google.datastore.Entity
            the entity of the id from datastore
    """
    entity = client.get(client.key(kind, id))
    if entity is None:
        raise RequestException({
            "code": "invalid_id",
            "description": "The id does not exist."
        }, 404)
    return entity

def get_task_by_id(task_id, user_id):
    """
    Get a task entity by task_id. Raise RequestException when the
    task id is invalid or the owner of the task does not match with
    the user_id.

    Parameters
        task_id : int
            datastore id of the task
        user_id : str
            user id from the app
    Returns:
        task : google.datastore.Entity
            a datastore Entity object represents a task.
            It contains the datastore and properties of the task.
    """
    task = get_entity_by_id("tasks", task_id)        
    if task["owner"] != user_id:
        raise RequestException({
            "code": "forbidden",
            "description": "You are not permitted to view/modify the task."
        }, 403)
    return task

def get_task_list_by_id(task_list_id, user_id=None):
    """
    Get a task list entity by task_list_id. Raise RequestException when the
    task_list_id is invalid. If the user_id does not match with the owner of
    the task list, return the task list only if the 'public' property of the
    task list is true. Otherwise, it will raise a RequestException.

    Parameters
        task_list_id : int
            datastore id of the task list
        user_id : str
            user id from the app. Default is None. It is None when the auth
            validation has failed. (See validations.auth)
    Returns:
        task_list : google.datastore.Entity
            a datastore Entity object represents a task.
            It contains the datastore and properties of the task.
    """
    task_list = get_entity_by_id("lists", task_list_id)
    if user_id != None and task_list["owner"] == user_id:
        return task_list
    if task_list["public"] == True and \
        request.endpoint == 'list_api.list_get_by_id':
        return task_list

    raise RequestException({
        "code": "forbidden",
        "description": "You are not permitted to view/modify the list."
    }, 403)


##############################################################################
# Get a Collection                                                           #
##############################################################################

def get_users():
    """
    Return users from datastore

    Returns:
        query : list
            a list of user entities    
    """
    query = client.query(kind="users")
    query = list(query.fetch())
    return query

def get_tasks(offset, user_id):
    """
    Returns list of tasks of the user_id. The list contains maximum
    PAGE_LIMIT number of tasks starting the task at offset in datastore.

    Parameters
        offset : int
            position of a task in datastore
        user_id : str
            user id of the app.
    Returns:
        query : list
            list of task entities from datastore
        total: int
            the total number of tasks in datastore        
    """
    query = client.query(kind="tasks")
    query = query.add_filter('owner', '=', user_id)
    total = len(list(query.fetch()))
    query = query.fetch(limit=PAGE_LIMIT, offset=offset)
    return list(query), total
    
def get_task_lists(offset, user_id=None):
    """
    Returns list of task lists of the user_id. The returned list contains
    maximum PAGE_LIMIT number of lists starting the list at offset
    in datastore. If user_id is None, returns a collection of public task
    lists.

    Parameters
        offset : int
            position of a task list in datastore
        user_id : str
            user id of the app. Default is None.
    Returns:
        query : list
            list of task list entities from datastore
        total: int
            the total number of task lists in datastore        
    """
    query = client.query(kind="lists")
    if user_id is None:
        query = query.add_filter('public', '=', True)
    else:
        query = query.add_filter('owner', "=", user_id)     
    total = len(list(query.fetch()))
    query = query.fetch(limit=PAGE_LIMIT, offset=offset)
    return list(query), total


##############################################################################
# Update an Entity                                                           #
##############################################################################
def update_task(task_id, task_property, user_id):
    """
    Update a task entity from datastore. If the request method is PUT,
    it checks whether the task_property contains all the required properties.

    Parameters:
        task_id : int
            the datastore id of the task
        task_property : dict
            key-value pairs of the new property values of the task
        user_id : str
            the user's id from the app
    Returns:
        task : google.datastore.Entity
            the updated task Entity object from datastore.
    """
    if request.method == 'PUT':
        validate_required("tasks", task_property)
    validate_task_property(task_property)
    task = get_task_by_id(task_id, user_id)
    for p in TASK_REQUIRED_PROPERTIES + ['completed']:
        if p in task_property:
            task[p] = task_property[p]
    client.put(task)
    return task

def update_task_list(list_id, task_list_property, user_id):
    """
    Update a task list entity from datastore. If the request method is PUT,
    it checks whether the task_list property contains all the required
    properties.

    Parameters:
        list_id : int
            the datastore id of the task list
        task_list_property : dict
            key-value pairs of the new property values of the task list
        user_id : str
            the user's id from the app
    Returns:
        task : google.datastore.Entity
            the updated task list Entity object from datastore.
    """
    if request.method == 'PUT':
        validate_required("lists", task_list_property)
    validate_task_list_property(task_list_property)
    task_list = get_task_list_by_id(list_id, user_id)

    # Check duplicate name
    if 'name' in task_list_property:
        name = task_list_property["name"]
        user_id = task_list["owner"]
        result = get_list_same_name(name, user_id)
        if len(result) > 0 and result[0].key.id != list_id:
            raise RequestException({
                "code": "list_name_not_unique",
                "description": "You already have a list with the same name."
            }, 403)

    for p in LIST_REQUIRED_PROPERTIES:
        if p in task_list_property:
            task_list[p] = task_list_property[p]
    client.put(task_list)
    return task_list
            
def update_entity_rel(entity):
    """
    Takes an entity and update it to datastore. Helper function for the
    relationship routes of task and task_list.

    Parameters
         entity : google.datastore.Entity
            an entity from datastore. It can be either a task or a (task) list
            entity.
    """
    client.put(entity)


##############################################################################
# Delete an Entity                                                           #
##############################################################################

def delete_task(task_id, user_id):
    """
    Delete a task entity from datastore. If there's a list related to the
    task, it removes the list's infomation from the list's tasks property
    before the task entity is deleted.

    Parameters:
        task_id : int
            the datastore id of the task
        user_id : str
            the user's id of the app.
    """
    task = get_task_by_id(task_id, user_id)
    # Remove this task from the task list.
    if task['task_list'] != {}:
        list_id = task['task_list']['id']
        task_list = get_task_list_by_id(list_id, user_id)
        for t in task_list['tasks']:
            if t['id'] == task_id:
                task_list['tasks'].remove(t)
                break
        client.put(task_list)
    client.delete(client.key("tasks", task_id))

def delete_task_list(list_id, user_id):
    """
    Delete the task list from datastore. Any tasks related to the list will
    be deleted from datastore.

    Parameters:
        list_id : int
            the datastore id of the task list
        user_id : str
            the user's id of the app
    """
    task_list = get_task_list_by_id(list_id, user_id)
    # Remove all tasks
    tasks = task_list['tasks']
    for task in tasks:
        task_id = task['id']
        client.delete(client.key("tasks", task_id))
    client.delete(client.key("lists", list_id))
