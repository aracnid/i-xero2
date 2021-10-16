"""Class module to interface with Xero.
"""
from functools import wraps

from aracnid_logger import Logger
from flask_oauthlib.contrib.client import OAuth, OAuth2Application
from i_mongodb import MongoDBInterface
from xero_python.accounting import AccountingApi
from xero_python.api_client import ApiClient, serialize
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.identity import IdentityApi

# initialize logger
logger = Logger(__name__).get_logger()


class XeroInterfaceUI:
    """Interface to Xero (xero-python).

    Environment Variables:
        None.

    Attributes:
        flask_app: Flask application.
        oauth_app: OAuth application.
        client: Xero client.
        tenant_id: Xero organization identifier.
    """

    def __init__(self, flask_app, mdb=None) -> None:
        """Initializes the Xero interface.

        Args:
            flask_app: Flask application.
        """
        self.flask_app = flask_app
        self.client = self.get_client()
        self.set_oauth_app(flask_app)
        self.tenant_id = None

        # initialize mongodb for token storage
        self.mdb = mdb
        if not mdb:
            self.mdb = MongoDBInterface()

    def xero_token_required(function):
        """Decorator function to ensure obtain xero token.
        """
        @wraps(function)
        def decorator(self, *args, **kwargs):
            xero_token = self.obtain_xero_oauth2_token()
            if not xero_token:
                return None

            return function(self, *args, **kwargs)

        return decorator

    def set_oauth_app(self, flask_app):
        """Configures and returns an OAuth app for the specified flask app.

        Args:
            flask_app: Flask application

        Returns:
            OAuth application
        """
        # TODO fetch config from https://identity.xero.com/.well-known/openid-configuration #1
        oauth = OAuth(flask_app)
        self.oauth_app = oauth.remote_app(
            name="xero",
            version="2",
            client_id=flask_app.config["CLIENT_ID"],
            client_secret=flask_app.config["CLIENT_SECRET"],
            endpoint_url="https://api.xero.com/",
            authorization_url="https://login.xero.com/identity/connect/authorize",
            access_token_url="https://identity.xero.com/connect/token",
            refresh_token_url="https://identity.xero.com/connect/token",
            scope="offline_access openid profile email accounting.transactions "
            "accounting.reports.read accounting.journals.read accounting.settings "
            "accounting.contacts accounting.attachments assets projects",
        )  # type: OAuth2Application

        # register token getter/saver
        self.oauth_app.tokengetter(self.client.oauth2_token_getter)
        self.oauth_app.tokensaver(self.client.oauth2_token_saver)

    def get_client(self):
        """Returns Xero client.

        Args:
            None.

        Returns:
            Xero client.
        """
        xero_api_client = ApiClient(
            Configuration(
                debug=self.flask_app.config["DEBUG"],
                oauth2_token=OAuth2Token(
                    client_id=self.flask_app.config["CLIENT_ID"], 
                    client_secret=self.flask_app.config["CLIENT_SECRET"]
                ),
            ),
            pool_threads=1,
        )

        # register token getter/saver
        xero_api_client.oauth2_token_getter(self.obtain_xero_oauth2_token)
        xero_api_client.oauth2_token_saver(self.store_xero_oauth2_token)

        return xero_api_client

    def get_oauth2_token(self):
        token = self.mdb.read_collection('xero_token').find_one(
            filter={'_id': 'token'}
        )

        # remove mongodb id
        if token:
            token.pop('_id')

        return token

    def obtain_xero_oauth2_token(self):
        """Configures token persistence
        
        This is the exchange point between flask-oauthlib and xero-python.

        Args:
            None.        
        """
        return self.oauth_app.tokengetter(
            self.client.oauth2_token_getter(
                self.get_oauth2_token
            )
        )()

    def store_oauth2_token(self, token):
        if token:
            self.mdb.read_collection('xero_token').replace_one(
                filter={'_id': 'token'},
                replacement=token,
                upsert=True
            )
        else:
            self.mdb.read_collection('xero_token').delete_one(
                filter={'_id': 'token'}
            )
    
    def store_xero_oauth2_token(self, token):
        """Stores the token.

        Args:
            token: Xero token.
        """

        self.oauth_app.tokensaver(
            self.client.oauth2_token_saver(
                self.store_oauth2_token
            )
        )(token)

    @xero_token_required
    def get_tenants(self):
        """Retrieves tenants from Xero api.

        This is an example method.
        """
        identity_api = IdentityApi(self.client)
        accounting_api = AccountingApi(self.client)

        available_tenants = []
        for connection in identity_api.get_connections():
            tenant = serialize(connection)
            if connection.tenant_type == "ORGANISATION":
                organisations = accounting_api.get_organisations(
                    xero_tenant_id=connection.tenant_id
                )
                tenant["organisations"] = serialize(organisations)

            available_tenants.append(tenant)

        return available_tenants

    def get_xero_tenant_id(self):
        """Retrieves the tenant ID.

        Retrieves the tenant ID if not already known, otherwise,
        it returns the previously retrieved information.
        """
        if self.tenant_id:
            return self.tenant_id

        token = self.obtain_xero_oauth2_token()
        if not token:
            return None

        identity_api = IdentityApi(self.client)
        for connection in identity_api.get_connections():
            if connection.tenant_type == "ORGANISATION":
                self.tenant_id = connection.tenant_id
                return self.tenant_id
        
    @xero_token_required
    def get_invoices(self):
        """Retrieves invoices from Xero api.

        This is an example method.
        """
        xero_tenant_id = self.get_xero_tenant_id()
        accounting_api = AccountingApi(self.client)

        invoices = accounting_api.get_invoices(
            xero_tenant_id, statuses=["DRAFT", "SUBMITTED"]
        )

        return invoices

    @xero_token_required
    def refresh_token(self):
        """Refreshes the token.

        Returns:
            Xero token.
        """
        self.client.oauth2_token_saver(
            self.store_oauth2_token
        )

        new_token = self.client.refresh_oauth2_token()

        return new_token
        