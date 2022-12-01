from pymongo import MongoClient
from flask import Flask, url_for, redirect, request, render_template, jsonify
import json
from bson.json_util import loads, dumps, default
from bson import ObjectId
from yaml import SafeLoader, FullLoader
import yaml
from ruamel.yaml import YAML, util, comments
import sys
from rasa.nlu.convert import convert_training_data
from rasa import train
from flask_socketio import SocketIO, send, join_room, leave_room
from flask_cors import CORS
from flask_session import Session
from datetime import datetime
from operator import itemgetter

users = {}

app = Flask(__name__)
CORS(app)
socket = SocketIO(app, cors_allowed_origins="*", wait=True, wait_timeout=5)

# database
client = MongoClient(
    'mongodb+srv://root:YmaXmz16j8AfLi94@cluster1.lcpgfzf.mongodb.net/?retryWrites=true&w=majority')
db = client['FirstDB']
chats = db.chats
# runserver
if __name__ == '__main__':
    socket.run(app, debug=True)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)


# chat frontend

@app.route('/chat', methods=['GET'])
def conversation():
    return render_template('index.html')

# socket connect


@socket.on('connect')
def connect(message):
    print('received message')
    print(users)
    # send(message)


@socket.on('disconnect')
def disconnect():
    print('disconnected')
# get previous chat from previus chat


@socket.on('get_details')
def get_details(data):
    users[data['sender']] = request.sid
    print('hi')
    sender = data['sender']
    receiver = data['receiver']
    send_messages = chats.find({'sender': sender, 'receiver': receiver})
    received_messages = chats.find({'receiver': sender, 'sender': receiver})
    messages = []
    for message in send_messages:
        messages.append(message)
    for message in received_messages:
        messages.append(message)
    messages = sorted(messages, key=itemgetter('created_at'))
    print(messages)
    messages = JSONEncoder().encode(messages)
    socket.emit('details', messages, room=request.sid)
    print(users)

# send message


@socket.on('send_message')
def handle_send_message_event(data):
    time = datetime.now()
    chats.insert_one(
        {'sender': data['sender_id'], 'message': data['message'], 'receiver': data['receiver_id'], 'created_at': time})
    data['type'] = 'received'
    if data['receiver_id'] in users:
        receiver_id = users[data['receiver_id']]
        socket.emit('receive_message', data, room=receiver_id)
    data['type'] = 'send'
    socket.emit('receive_message', data, room=request.sid)
    # socket.emit('receive message', data, room=rq)


# rasa chatbot


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)


@app.route('/intent', methods=['POST'])
def train_data():
    data = request.data
    data = json.loads(data)

    if data['intent'] and data['action']:
        with open('../domain.yml') as domain_file:
            if data['intent'] in domain['intent']:
                return {'status': 'failure', 'data': 'intent altready exits'}
            if data['action'] in domain['responses']:
                return {'status': 'failure', 'data': 'action altready exits'}
        # updating nlu
        with open('../data/nlu.yml', 'a') as nlu:
            nlu.write(
                "\n  - intent: {}\n    examples: |".format(data['intent']))
            for i in data['examples']:
                nlu.write("\n      - {}".format(i))

        # updating domain
        domain = None
        with open('../domain.yml') as domain_file:
            yaml2 = YAML()
            config, ind, bsi = util.load_yaml_guess_indent(
                open('../domain.yml'))
            domain = yaml.load(domain_file, Loader=SafeLoader)
            yaml2.indent(sequence=ind, offset=bsi)
            yaml2.sort_key = False
            yaml2.preserve_quotes = True
            domain['intents'].append(data['intent'])
            domain['responses'][data['action']] = [
                {'text': data['action_text']}]

        with open("../domain.yml", "w") as domain_file:
            yaml2.indent(mapping=2, sequence=3, offset=1)
            yaml2.dump(domain, domain_file)

    # updating stories file

    if data['intent'] and data['action'] or data['story_heading'] and data['story']:
        with open('../data/stories.yml', 'a') as stories_file:
            stories_file.write(
                '\n- story: {}\n  steps:\n'.format(data['story_heading']))
            if data['story']:
                for story in data['story']:
                    stories_file.write(
                        '  - intent: {}\n  - action: {}\n'.format(story['intent'], story['action']))
            else:
                stories_file.write(
                    '  - intent: {}\n  - action: {}\n'.format(data['intent'], data['action']))
    # train data
    result = train(domain='../domain.yml', config='../config.yml', training_files=[
                   '../data/nlu.yml', '../data/stories.yml'], output='../models/', dry_run=False, force_training=False, fixed_model_name=None, persist_nlu_training_data=False)
    return {'status': 'success', 'data': result}
