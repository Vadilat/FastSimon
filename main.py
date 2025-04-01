import json

from flask import Flask, request
from google.cloud import datastore

app = Flask(__name__) #create flask app
datastore_client = datastore.Client()   #create datastore client

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/set')
def set_variable():
    name = request.args.get('name')
    value = request.args.get('value')

    if not name or value is None:
        return error("Missing name or value")

    key = datastore_client.key("Variable", name)    #Creates a key of kind "Variable" with ID = name
    existing_entity = datastore_client.get(key)  #get value before it's updated
    prev_value = existing_entity["value"] if existing_entity else None

    entity = datastore.Entity(key=key)
    entity["value"] = value
    datastore_client.put(entity)


    # update undo history
    history = get_history()  # get the history entity
    undo_stack = json.loads(history["undo_stack"])  # Load it as a Python list

    # add current action to the undo stack
    undo_stack.append({
        "command": "SET",
        "name": name,
        "prev": prev_value,
        "curr": value
    })

    # save updated history back to Datastore
    history["undo_stack"] = json.dumps(undo_stack)  # Store as string
    history["redo_stack"] = json.dumps([])  # Clear redo stack
    save_history(history)

    return ok(f"{name} = {value}")

@app.route('/get')
def get_variable():
    name = request.args.get('name') #get name from url

    if not name:
        return error("Error: Missing 'name' parameter.")

    key = datastore_client.key("Variable", name)  # Creates a key of kind "Variable" with ID = name
    entity = datastore_client.get(key)


    if entity:
        value = entity.get('value')  # Access the 'value' property of the retrieved entity
        return ok(str(value))
    else:
        return ok("None")

@app.route('/unset')
def unset_variable():
    name = request.args.get('name')  # get name from url

    if not name:
        return error("Error: Missing 'name' parameter.")

    key = datastore_client.key("Variable", name)
    existing_entity = datastore_client.get(key)  # get value before it's deleted

    prev_value = existing_entity["value"] if existing_entity else None

    datastore_client.delete(key)  # delete the entity if it exists

    # update undo history
    history = get_history()
    undo_stack = json.loads(history["undo_stack"])

    undo_stack.append({
        "command": "UNSET",
        "name": name,
        "prev": prev_value,
        "curr": None
    })

    history["undo_stack"] = json.dumps(undo_stack)
    history["redo_stack"] = json.dumps([])  # clear redo stack
    save_history(history)

    return ok(f"{name} = None")

@app.route('/numequalto')
def num_equal_to_variable():
    value = request.args.get('value') #get name from url

    if not value:
        return error("Error: Missing 'value' parameter.")

    # Create a query on kind "Variable" where 'value' == {value}
    query = datastore_client.query(kind="Variable")
    query.add_filter(filter=("value", "=", value))
    query_res = list(query.fetch()) #put result to list

    return ok(str(len(query_res)))

@app.route('/undo')
def undo_variable():
    history = get_history()
    undo_stack = json.loads(history["undo_stack"])
    redo_stack = json.loads(history["redo_stack"])

    if not undo_stack:
        return ok("NO COMMANDS")

    # Pop the last command
    undo = undo_stack.pop()
    command = undo["command"]
    name = undo["name"]
    prev = undo["prev"]

    key = datastore_client.key("Variable", name)

    # Reverse the action
    if command == "SET":
        if prev is None:
            # It was a new variable — so delete it
            datastore_client.delete(key)
            output = f"{name} = None"
        else:
            # Revert to the previous value
            entity = datastore.Entity(key=key)
            entity["value"] = prev
            datastore_client.put(entity)
            output = f"{name} = {prev}"
    elif command == "UNSET":
        # Restore the previous value
        if prev is not None:
            entity = datastore.Entity(key=key)
            entity["value"] = prev
            datastore_client.put(entity)
            output = f"{name} = {prev}"
        else:
            datastore_client.delete(key)
            output = f"{name} = None"
    else:
        return error(f"Unsupported command: {command}")

    # Push the reversed command to the redo stack
    redo_stack.append(undo)

    # Save updated history
    history["undo_stack"] = json.dumps(undo_stack)
    history["redo_stack"] = json.dumps(redo_stack)
    save_history(history)

    return ok(output)

@app.route('/redo')
def redo_variable():
    history = get_history()
    undo_stack = json.loads(history["undo_stack"])
    redo_stack = json.loads(history["redo_stack"])

    if not redo_stack:
        return ok("NO COMMANDS")

    redo = redo_stack.pop()
    command = redo["command"]
    name = redo["name"]
    curr = redo["curr"]

    key = datastore_client.key("Variable", name)

    if command == "SET":
        entity = datastore.Entity(key=key)
        entity["value"] = curr
        datastore_client.put(entity)
        output = f"{name} = {curr}"
    elif command == "UNSET":
        datastore_client.delete(key)
        output = f"{name} = None"
    else:
        return error(f"Unsupported command: {command}")
    # Push this command back to undo stack
    undo_stack.append(redo)

    # Save updated stacks
    history["undo_stack"] = json.dumps(undo_stack)
    history["redo_stack"] = json.dumps(redo_stack)
    save_history(history)

    return ok(output)

@app.route('/end')
def end_program():
    # Delete all entities of kind "Variable"
    kind_variable = datastore_client.query(kind="Variable")
    keys_variable = [entity.key for entity in kind_variable.fetch()]
    if keys_variable:
        datastore_client.delete_multi(keys_variable)

    # Delete the "History" singleton entity
    key_history = datastore_client.key("History", "log")
    datastore_client.delete(key_history)

    return ok("CLEANED")

#show all variables
@app.route('/list')
def list_variables():
    query = datastore_client.query(kind="Variable")
    entities = list(query.fetch())
    result = {e.key.name: e['value'] for e in entities}
    return ok(json.dumps(result))

# helper functions
def ok(msg):
    return msg, 200

def error(msg):
    return msg, 400

def get_history():  #refer to history as a dict and transfer back and forth using json dump and json load
    key = datastore_client.key("History", "log")
    history = datastore_client.get(key)

    if not history: #if doesn't exist - create history
        history = datastore.Entity(key=key)
        history["undo_stack"] = json.dumps([])
        history["redo_stack"] = json.dumps([])
        datastore_client.put(history)
    return history

def save_history(history):
    datastore_client.put(history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
