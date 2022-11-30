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
    # print(request.sid)
    print('received message')
    send(message)

# join room


@socket.on('join_room')
def handle_join_room_event(data):
    print(data['room'], data, 'da')
    app.logger.info("{} has joined the room {}".format(
        data['username'], data['room']))
    join_room(data['room'])


@socket.on('get_details')
def get_details(data):
    # if 'id' in data:
    users[data['sender']] = request.sid
    sender = data['sender']
    receiver = data['receiver']
    chat1 = chats.find({'sender': sender, 'receiver': receiver})
    chat2 = chats.find({'receiver': sender, 'sender': receiver})
    chat = []
    for i in chat1:
        chat.append(i)
    for i in chat2:
        chat.append(i)
    newlist = sorted(chat, key=itemgetter('created_at'))
    print('break')
    for i in newlist:
        print(i)
    print(type(newlist))
    data = dumps(newlist)
    newlist = loads(data)
    newlist = JSONEncoder().encode(newlist)
    print(newlist)
    if receiver in users:
        receiver_id = users[receiver]
        socket.emit('details', newlist, room=receiver_id)
    if sender in users:
        sender_id = users[sender]
        socket.emit('details', newlist, room=sender_id)
# print(chat1, 'hi', chat2, chat)


# @socket.on('send_username')
# def get_username(data):
#     # users.append({data['id']: request.sid})

#     # message


@socket.on('send_message')
def handle_send_message_event(data):
    print(data)
    time = datetime.now()
    chats.insert_one(
        {'sender': data['sender_id'], 'message': data['message'], 'receiver': data['receiver_id'], 'created_at': time})
    if data['receiver_id'] in users:
        receiver_id = users[data['receiver_id']]
        socket.emit('receive_message', data, room=receiver_id)


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
