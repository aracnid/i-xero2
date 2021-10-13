# import modules
import os

from aracnid_logger import Logger
from i_mongodb import MongoDBInterface
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from pytz import timezone, utc
from xero import Xero
from xero.auth import OAuth2Credentials

# initialize logging
logger = Logger(__name__).get_logger()

est = timezone('US/Eastern')


class XeroInterface:
    """Interface to Xero (pyxero).

    Environment Variables:
        XERO_CLIENT_ID: Xero OAuth2 Client ID.
        XERO_CLIENT_SECRET: Xero OAuth2 Client Secret.

    Attributes:
        TBD.
    """
    instances = []

    # initialize xero
    def __init__(self, mdb=None):
        """Initializes the XeroInterface class.

        Args:
            mdb: A reference to a MongoDBInterface object.
        """
        logger.debug('init_xero()')
        
        # initialize mongodb for token storage
        self.mdb = mdb
        if not mdb:
            self.mdb = MongoDBInterface()

        # create credentials
        self.client_id = os.environ.get('XERO_CLIENT_ID')
        self.client_secret = os.environ.get('XERO_CLIENT_SECRET')
        self.scope_list = self.get_scopes()

        # set the xero client
        self.set_client()

        # track class instances
        XeroInterface.instances.append(self)
        logger.debug(f'XeroInterface.instances: {len(XeroInterface.instances)}')

    def set_client(self):
        token = self.get_token()
        logger.debug(f'[setup] expires: {token["expires_at"]}')

        if token:
            self.credentials = OAuth2Credentials(
                client_id=self.client_id,
                client_secret=self.client_secret,
                scope=self.scope_list,
                token=token
            )

            # check for expired token
            if self.credentials.expired():
                self.refresh_token()

            self.credentials.set_default_tenant()

            # authenticate
            self.client = Xero(self.credentials)

        else:
            self.client = None
            self.notify_to_reauthorize()

    @staticmethod
    def notify_to_reauthorize():
        oauth2_url = os.environ.get('XERO_OAUTH2_URL')
        logger.error(f'NEED TO REAUTHORIZE XERO: {oauth2_url}')

    def get_client(self):
        return self.client

    def get_token(self):
        token = self.mdb.read_collection('xero_token').find_one(
            filter={'_id': 'token'}
        )

        # remove mongodb id
        if token:
            token.pop('_id')

        return token

    def save_token(self, token):
        self.mdb.read_collection('xero_token').replace_one(
            filter={'_id': 'token'},
            replacement=token,
            upsert=True
        )

    def refresh_token(self):
        token = self.credentials.token
        # logger.debug(f'[refresh] token id: {token["id_token"]}')
        logger.debug(f'[refresh] expires: {token["expires_at"]}')

        self.credentials.refresh()
        new_token = self.credentials.token
        self.save_token(new_token)
        logger.info('Refreshed Xero token')
        logger.debug(f'[refresh] expires: {new_token["expires_at"]}')

    def get_scopes(self):
        scopes = os.environ.get('XERO_SCOPES')
        scope_list = scopes.split(',')

        return scope_list

    @staticmethod
    def get_xero_datetime(dt):
        if dt:
            if dt.tzinfo:
                return dt.astimezone(est)
            else:
                # return utc.localize(dt).astimezone(timezone('US/Eastern'))
                return est.localize(dt)
        return None

    @staticmethod
    def get_xero_datetime_utc(dt):
        if dt:
            if dt.tzinfo:
                return dt.astimezone(utc)
            else:
                # return utc.localize(dt).astimezone(utc)
                return utc.localize(dt)
        return None

    def get_invoice(self, invoice_id):
        invoice = None

        try:
            invoice = self.client.invoices.get(invoice_id)[0]
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            invoice = self.client.invoices.get(invoice_id)[0]

        return invoice

    def get_invoices(self, **kwargs):
        invoices = None

        try:
            invoices = self.client.invoices.filter(**kwargs)
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            invoices = self.client.invoices.filter(**kwargs)

        return invoices

    def get_repeating_invoice(self, invoice_id):
        invoice = None

        try:
            invoice = self.client.repeatinginvoices.get(invoice_id)[0]
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            invoice = self.client.repeatinginvoices.get(invoice_id)[0]

        return invoice

    def get_repeating_invoices(self, **kwargs):
        invoices = None

        try:
            invoices = self.client.repeatinginvoices.filter(**kwargs)
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            invoices = self.client.repeatinginvoices.filter(**kwargs)

        return invoices

    def get_item(self, item_id):
        item = None

        try:
            item = self.client.items.get(item_id)[0]
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            item = self.client.items.get(item_id)[0]

        return item

    def get_items(self, **kwargs):
        items = None

        try:
            if len(kwargs) == 0:
                items = self.client.items.all()
            else:
                items = self.client.items.filter(**kwargs)
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            if len(kwargs) == 0:
                items = self.client.items.all()
            else:
                items = self.client.items.filter(**kwargs)

        return items

    def set_payments(self, payment_list):
        try:
            self.client.payments.put(payment_list)
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            self.client.payments.put(payment_list)

    def get_organizations(self):
        organizations = None

        try:
            organizations = self.client.organisations.all()
        except AttributeError:
            self.notify_to_reauthorize()
        except TokenExpiredError:
            self.refresh_token()
            organizations = self.client.organisations.all()

        return organizations
