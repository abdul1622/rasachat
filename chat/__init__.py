from flask import Flask
from os import path
# Import for Migrations


def create_app():
    app = Flask(__name__)

    return app
