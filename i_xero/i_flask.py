"""Class module to interface with Flask.
"""
import os
from os.path import dirname, join

from flask import Flask
from flask_session import Session
from i_mongodb import MongoDBInterface


class FlaskInterface:
    """Interface to Flask.

    Environment Variables:
        CLIENT_ID: OAuth client ID.
        CLIENT_SECRET: OAuth client secret.

    Attributes:
        name: Name of the Flask application.
        app: Flask application.
    """
    def __init__(self, name, mdb=None) -> None:
        """Initializes the Flask interface.

        Args:
            name: Name of the Flask application.
            mdb: A reference to a MongoDBInterface object.
        """
        self.name = name
        self.app = Flask(name)
        self.mdb = mdb
        if not mdb:
            self.mdb = MongoDBInterface()

        # config flask session
        flask_session_type = os.environ.get('FLASK_SESSION_TYPE')
        self.app.config['SESSION_TYPE'] = flask_session_type
        if flask_session_type == 'filesystem':
            self.app.config['SESSION_FILE_DIR'] = join(dirname(dirname(__file__)), 'cache')
        elif flask_session_type == 'mongodb':
            self.app.config['SESSION_MONGODB'] = self.mdb.mongo_client
            self.app.config['SESSION_MONGODB_DB'] = os.environ.get('MONGODB_DBNAME')
            self.app.config['SESSION_MONGODB_COLLECT'] = 'xero_token'

        self.app.config['SECRET_KEY'] = os.urandom(16)
        self.app.config['CLIENT_ID'] = os.environ.get('XERO_CLIENT_ID') or ''
        self.app.config['CLIENT_SECRET'] = os.environ.get('XERO_CLIENT_SECRET') or ''
        self.app.config['ENV'] = os.environ.get('FLASK_DEPLOYMENT_TYPE') or 'development'
        if self.app.config["ENV"] != "production":
            # allow oauth2 loop to run over http (used for local testing only)
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        # configure persistent session cache
        Session(self.app)

    def get_app(self):
        """Returns the Flask application object.

        Returns:
            Flask application object.
        """
        return self.app
