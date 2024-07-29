from flask import make_response, request
from datetime import datetime
from constants.constants import TASK_REQUIRED_PROPERTIES
from constants.constants import LIST_REQUIRED_PROPERTIES
from constants.constants import MAX_LIST_NAME_LEN


class BadRequest(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

def handle_bad_request(err):
    """
    Handles the app's 400 BadRequest Error.
    """
    return make_response(err.error, err.status_code)

def validate_required(kind, property):
    """
    Check if the request has all required properties.

    Parameters
        kind : str
            a string key for google datastore. Use it to determine which
            resource is this validation for.
        property : dict
            key-value pairs of properties of a resource
    
    """
    required = {
        "tasks": TASK_REQUIRED_PROPERTIES,
        "lists": LIST_REQUIRED_PROPERTIES
    }
    required_property = required[kind]

    # For PUT /tasks/:task_id. The 'completed' property is not in constants.py
    if request.endpoint == 'task_api.task_patch_put' and \
        request.method == "PUT":
        required_property.append("completed")

    for p in required_property:
        if p not in property:
            raise BadRequest({
                "code": "required_property_missing",
                "description": "One of the required properties is missing."
            }, 400)
           

def validate_task_property(task_property):
    """
    Validate task's properties.
    - due_date should be in the format of Y-M-D, and the type should be
      able tp parsed by datetime module. e.g. 23/13/1. - raise 400,
        there is no month #13.
    - check types of bool to be able to parse it.

    Parameters
        task_property: dict
            key-value paris of task properties
    """
    if 'due_date' in task_property:
        # Check due_date
        try:
            datetime.strptime(task_property['due_date'], '%Y-%m-%d')
        except ValueError:
            raise BadRequest({
                "code": "invalid_due_date",
                "description": "Cannot parse the due_date."
            }, 400)            

    # Check completed - for task_patch_put route only.
    if request.endpoint == 'task_api.task_patch_put' and \
        'completed' in task_property and \
        type(task_property['completed']) != bool:
        raise BadRequest({
            "code": "invalid_completed",
            "description": "Cannot parse the completed value."
        }, 400)            

def validate_task_list_property(list_property):
    """
    Validate task list's properties.
    - name should be less than the number of characters set to
      MAX_LIST_NAME_LEN in config.config
    - public value should be a bool so that the program can parse it.

    Parameters
        task_list_property: dict
            key-value paris of task list properties
    """
    # Check name
    if 'name' in list_property and \
        len(list_property['name']) > MAX_LIST_NAME_LEN:
        raise BadRequest({
            "code": "invalid_list_name",
            "description": f"The list name exceeds {MAX_LIST_NAME_LEN} characters."
        }, 400)
    
    # Check public
    if 'public' in list_property and \
        type(list_property['public']) != bool:
        raise BadRequest({
            "code": "invlalid_public",
            "description": "Cannot parse the public value."
        }, 400)