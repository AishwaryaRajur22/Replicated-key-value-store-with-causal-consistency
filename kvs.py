from flask import Flask, request, jsonify
import requests
import json
import os
import time

# Flask application
app = Flask(__name__)

# key-value store dict
key_value_storage = {}

# Create Replicas
replicas = []

# Initialize vector clocks
vector_clock = {} 

current_address = ''

# View Operations Functions


# Handle PUT requests for view
@app.route('/view', methods=['PUT'])
def add_replica():
    replica_address = request.json.get('socket-address')

    if replica_address in replicas:
        return jsonify(result="already present"), 200
        
        
    # Add to replica list and add vector_clock entry
    replicas.append(replica_address)
    vector_clock[replica_address] = 0
    
    return jsonify(result="added"), 201

# Handle GET requests for view
@app.route('/view', methods=['GET'])
def get_view():
    return jsonify(view=replicas), 200

# Handle DELETE requests for view
@app.route('/view', methods=['DELETE'])
def remove_replica():
    replica_address = request.json.get('socket-address')

    if replica_address not in replicas:
        return jsonify(error="View has no such replica"), 404
    # Remove from view
    replicas.remove(replica_address)
    del vector_clock[replica_address]
    return jsonify(result="deleted"), 200



# Key Value Operations
'''The do stuff functions'''

# Handle PUT requests for kvs
@app.route('/kvs/<key>', methods=['PUT'])
def put_key(key):
    data = request.json
    value = data.get('value')
    client_causal_metadata = data.get('causal-metadata')

    if len(key) > 50:
        return jsonify(error="Key is too long"), 400

    if value is None:
        return jsonify(error="Value is required"), 400

    if causally_consistent(client_causal_metadata) == False:
        return jsonify(error="Causal dependencies not satisfied"), 503
    
    
    # Select correct response
    put_result = "created"
    put_code = 201
    if key in key_value_storage:
        put_result = "replaced"
        put_code = 200

    # Update kv store
    key_value_storage[key] = value
    vector_clock[current_address] += 1

    # Broadcast update
    broadcast_update({'key': key, 'value': value, 'op': 'PUT', 'vector_clock': vector_clock.copy()})
    return {'result':put_result, "causal-metadata":vector_clock.copy()}, put_code

# Handle GET requests for kvs
@app.route('/kvs/<key>', methods=['GET'])
def get_key(key):
    client_causal_metadata = request.json.get('causal-metadata')

    if causally_consistent(client_causal_metadata) == False:
        return jsonify(error="Causal dependencies not satisfied"), 503

    value = key_value_storage.get(key)
    if value is None:
        return jsonify(error="Key does not exist"), 404
    print("CURRENT KVS:" + str(key_value_storage))
    return{'result':"found", 'value':value, "causal-metadata":vector_clock.copy()}, 200

# Handle DELETE requests for kvs
@app.route('/kvs/<key>', methods=['DELETE'])
def delete_key(key):
    client_causal_metadata = request.json.get('causal-metadata')
    
    if causally_consistent(client_causal_metadata) == False:
        return jsonify(error="Causal dependencies not satisfied"), 503

    if key not in key_value_storage:
        return jsonify(error="Key does not exist"), 404
    # Delete from kv store
    del key_value_storage[key]
    vector_clock[current_address] += 1

    # Broadcast deletion
    broadcast_update({'key': key, 'op': 'DELETE'})
    return {'result':'deleted', 'causal-metadata':vector_clock.copy()}, 200

@app.route('/brod/<key>', methods=['PUT','DELETE','GET'])
def receive_broadcast(key):
    print(request.method + " BROADCAST RECIEVED")
    if request.method == 'PUT':
        data = request.json
        value = data.get('value')
        # Select correct response
        put_result = "created"
        put_code = 201
        if key in key_value_storage:
            put_result = "replaced"
            put_code = 200

        # Update kv store
        key_value_storage[key] = value
        vector_clock[current_address] += 1
        return {'result':put_result, "causal-metadata":vector_clock.copy()}, put_code
    elif request.method == 'DELETE':

        del key_value_storage[key]
        vector_clock[current_address] += 1
        return {'result':'deleted', 'causal-metadata':vector_clock.copy()}, 200
    elif request.method == 'GET':
        print("GIVING KVS")
        return {'kvs':key_value_storage.copy(), 'causal-metadata':vector_clock.copy()}, 200

# Helper Functions


# Check for causall consistancy 
def causally_consistent(client_metadata):

    # Client first interaction
    if client_metadata == None:
        return True
    
    maxClock = max(client_metadata.values())
    if vector_clock[current_address]<maxClock:
        return False

    # Iterate over the replica vector clock
    '''
    for replica, replica_clock_value in vector_clock.items():
        client_clock_value = client_metadata.get(replica, 0)

        # Check if the client clock is behind the replica clock
        if client_clock_value < replica_clock_value:
            print(client_clock_value)
            print(replica_clock_value)
            return False
    '''
    # The client view is up-to-date or concurrent
    return True

# Broadcasts an update to all other replicas
def broadcast_update(broadcast_info):

    # Increment the replica clock
    
    # Iterate over the list of replicas
    for replica in replicas:
        # Skip sending the update to self
        if replica == current_address and broadcast_info['op'] != "DELETE":
            continue

        if broadcast_info['op'] == "PUT":
            print("broadcasting PUT")
            try:
                # Send the update to the replica
                response = requests.put('http://{}/brod/{}'.format(replica, broadcast_info['key']),json={'value':broadcast_info['value']}, timeout=10)
                #time.sleep(1)
                
                # Handle response if necessary
                if response.status_code >= 300:
                    pass
            except requests.exceptions.RequestException as exception:
                replicas.remove(replica)
                del vector_clock[replica]
                print(replicas)
                broadcast_update({'key': broadcast_info['key'], 'op': 'DELETE', 'address':replica})
        if broadcast_info['op'] == "DELETE":
            try:
                # Send the update to the replica
                print("Running delete on: " + replica + " to remove socket: " + broadcast_info['address'])
                response = requests.delete('http://{}/view'.format(replica) ,json={'socket-address':broadcast_info['address']})
                
                # Handle response if necessary
                if response.status_code >= 300:
                    # Code for unsuccessful broadcast goes here
                    pass
            except requests.exceptions.RequestException as exception:
                #Code for request Exception handling goes here
                #Replicas that give this error are down
                pass

# push context manually to app
with app.app_context():
    print("Running INIT:" + str(replicas))
    current_address = os.getenv('SOCKET_ADDRESS')
    replicas = os.getenv('VIEW').split(',')
    for replica in replicas:
        vector_clock[replica] = 0
        try:
            # Send the update to the 
            print("SENDING UPDATE TO" +  replica)
            update_response = requests.put('http://{}/view'.format(replica) ,json={'socket-address':current_address})
 
            # Increment the replica clock
            # Handle response if necessary
            if update_response.status_code >= 300:
                # Code for unsuccessful broadcast goes here
                pass
        except requests.exceptions.RequestException as exception:
            #Code for request Exception handling goes here
            #Replicas that give this error are down
            pass
    if len(replicas) > 0:
        if current_address !=replicas[0]:
            try:
                # Send the update to the 
                print("GETTING UPDATED LIST FROM: " +  replicas[0])
                response_json = requests.get('http://{}/brod/init'.format(replicas[0])).json()
                key_value_storage = response_json['kvs']
                vector_clock[current_address] = max(response_json['causal-metadata'].values())
                # Increment the replica clock
                # Handle response if necessary
            except requests.exceptions.RequestException as exception:
                #Code for request Exception handling goes here
                #Replicas that give this error are down
                pass
    print("KVS: " + str(key_value_storage))
    print("DONE INIT")

if __name__ == '__main__':

    # Start the Flask server
    app.run(host='0.0.0.0', port=8090)
