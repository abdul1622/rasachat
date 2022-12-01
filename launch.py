from chat.app import socket, app
from waitress import serve
from time import sleep
import logging
from paste.translogger import TransLogger
from threading import Thread
from actions import *
import os


def flask_server():
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    serve(TransLogger(app, setup_console_handler=False),
          host='127.0.0.1', port=8000)


def action_server():
    os.system('rasa run actions')


if __name__ == '__main__':
    flask_thread = Thread(target=flask_server)
    flask_thread.start()
    action_thread = Thread(target=action_server)
    action_thread.start()
    print('hi')
    os.system('rasa run -m models --enable-api --cors "*" --debug')
