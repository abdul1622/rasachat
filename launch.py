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


if __name__ == '__main__':
    thread = Thread(target=flask_server)
    thread.start()
    print('hi')
    os.system('docker-compose up')
