# task-manager-api

## About The Project

A RESTful API manages tasks and task lists with OAuth to handle the authentication.
Users can read, create, edit, and delete their tasks and task lists.

This is the final project of Oresgon State University's CS493 Cloud Application Development

### Features
- allow user to create account using 0Auth account
- create/manage tasks and task lists
- add/remove tasks to a task list
- tasks can be viewed by the owner only
- user can set a task list shown on public or keep it private.
- public task list and its tasks can be viewed by other people.

## How to Start
Note: You will need to create `config.py` in the root folder.
```
# config.py

class Config:
  APP_SECRET_KEY=<your_secret_key>
  AUTH0_CLIENT_ID=<your_auth0_client_id>
  AUTH0_CLIENT_SECRET=<your_auth0_client_secret>
  AUTH0_DOMAIN=<your_auth0_domain>
```

1. Clone the repository
```
git clone https://github.com/leahinosu/task-manager-api/
```
2. Create a virtual environment and activate it.
```
python -m venv venv
venv/Scripts/activate
```
3. Install requirements.
```
pip install -r requirements.txt
```
4. Run the api.
```
flask run
```
5. Open the index.html in the template folder to get your JWT token.
6. Use the token to interact with the api.
