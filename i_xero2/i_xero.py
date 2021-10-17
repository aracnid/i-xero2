# import modules
from datetime import date
import os

from aracnid_logger import Logger
from i_mongodb import MongoDBInterface
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from pytz import timezone, utc
from xero_python.accounting import AccountingApi
from xero_python.accounting import Invoice, Account, Payment
from xero_python.accounting import ManualJournals
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.exceptions import AccountingBadRequestException

# initialize logging
logger = Logger(__name__).get_logger()


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

        # initialize instance variables
        self.unitdp = 4
        self.tenant_id = os.environ.get('XERO_TENANT_ID')
        self.summarize_errors = False

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

        # set the APIs
        self.accounting_api = AccountingApi(self.client)

        # track class instances
        XeroInterface.instances.append(self)
        logger.debug(f'XeroInterface.instances: {len(XeroInterface.instances)}')

    def set_client(self):
        token = self.get_token()
        logger.debug(f'[setup] expires: {token["expires_at"]}')

        if token:
            # self.credentials = OAuth2Credentials(
            #     client_id=self.client_id,
            #     client_secret=self.client_secret,
            #     scope=self.scope_list,
            #     token=token
            # )
            self.client = ApiClient(
                Configuration(
                    debug=False,
                    oauth2_token=OAuth2Token(
                        client_id=self.client_id,
                        client_secret=self.client_secret
                    ),
                ),
                pool_threads=1,
            )
            # register token getter/saver
            self.client.oauth2_token_getter(self.obtain_xero_oauth2_token)
            self.client.oauth2_token_saver(self.store_xero_oauth2_token)

            self.client.set_oauth2_token(token)

            oauth2_token = self.client.configuration.oauth2_token
            # check for expired token
            if not oauth2_token.is_access_token_valid():
                oauth2_token.refresh_access_token(self.client)

        else:
            self.client = None
            self.notify_to_reauthorize()

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
        return self.client.oauth2_token_getter(
            self.get_oauth2_token
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

        self.client.oauth2_token_saver(
                self.store_oauth2_token
        )(token)

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
        est = timezone('US/Eastern')
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
        """Retrieves a specific sales invoice or purchase bill using a unique invoice Id.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            invoice_id: Invoice identifier.

        Returns:
            Dictionary of the specified invoice.
        """
        invoice = None
        
        try:
            api_response = self.accounting_api.get_invoice(
                self.tenant_id,
                unitdp=self.unitdp,
                invoice_id=invoice_id
            )
            invoice = api_response.invoices[0]
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return invoice

    def get_invoices(self, **kwargs):
        """Retrieves a list of invoices that conform to the specified parameters.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            if_modified_since: Invoices created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...
        """
        invoice_list = []
        
        try:
            api_response = self.accounting_api.get_invoices(
                self.tenant_id,
                unitdp=self.unitdp,
                **kwargs
            )
            invoice_list = api_response.invoices
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return invoice_list

    def get_item(self, item_id):
        """Retrieves a specific item using a unique item Id.

        Scopes:
            accounting.settings
            accounting.settings.read

        Args:
            item_id: Item identifier.

        Returns:
            Dictionary of the specified item.
        """
        item = None
        
        try:
            api_response = self.accounting_api.get_item(
                self.tenant_id,
                unitdp=self.unitdp,
                item_id=item_id
            )
            item = api_response.items[0]
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return item

    def get_items(self, **kwargs):
        """Retrieves a list of items that conform to the specified parameters.

        Scopes:
            accounting.settings
            accounting.settings.read

        Args:
            if_modified_since: Items created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...
        """
        item_list = []
        
        try:
            api_response = self.accounting_api.get_items(
                self.tenant_id,
                unitdp=self.unitdp,
                **kwargs,
            )
            item_list = api_response.items
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return item_list

    # MANUAL JOURNALS
    def create_manual_journals(self, manual_journal_list):
        """Creates one or more manual journals.

        Scopes:
            accounting.transactions

        Args:
            manual_journal_list: List of manual journals to create.

        Returns:
            List of created ManualJournal objects.
        """
        try:
            manual_journals = self.accounting_api.create_manual_journals(
                self.tenant_id,
                manual_journals=ManualJournals(
                    manual_journals=manual_journal_list
                )
            )
            return manual_journals.manual_journals
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def read_manual_journals(self, **kwargs):
        """Retrieves one or more manual journals.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            id: Identifier
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            Dictionary or list of retrieved manual journals.
        """
        id = kwargs.pop('id', None)
        
        try:
            if id:
                manual_journals = self.accounting_api.get_manual_journal(
                    self.tenant_id,
                    manual_journal_id=id
                )
                if len(manual_journals.manual_journals) == 1:
                    return manual_journals.manual_journals[0]
                else:
                    return None
            else:
                manual_journals = self.accounting_api.get_manual_journals(
                    self.tenant_id,
                    **kwargs,
                )
                return manual_journals.manual_journals
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def update_manual_journals(self, manual_journal_list):
        """Updates one or more manual journals.

        (Upsert) If a manual journal does not exist it will be created.

        Scopes:
            accounting.transactions

        Args:
            manual_journal_list: List of manual journals to update

        Returns:
            Dictionary or list of retrieved manual journals.
        """
        try:
            manual_journals = self.accounting_api.update_or_create_manual_journals(
                self.tenant_id,
                manual_journals=ManualJournals(
                    manual_journals=manual_journal_list
                )
            )
            return manual_journals.manual_journals
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def delete_manual_journals(self, **kwargs):
        """Deletes/voids one or more manual journals.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            manual_journals: List of ManualJournal objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted manual journals.
        """
        id = kwargs.pop('id', None)
        manual_journals = kwargs.pop('manual_journals', None)

        try:
            if id:
                manual_journal = self.read_manual_journals(id=id)
                if manual_journal.status == 'DRAFT':
                    manual_journal.status = 'DELETED'
                elif manual_journal.status == 'POSTED':
                    manual_journal.status = 'VOIDED'
                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=[manual_journal]
                )
            elif manual_journals:
                for manual_journal in manual_journals:
                    if manual_journal.status == 'DRAFT':
                        manual_journal.status = 'DELETED'
                    elif manual_journal.status == 'POSTED':
                        manual_journal.status = 'VOIDED'
                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=manual_journals
                )
            else:
                manual_journals = self.read_manual_journals(**kwargs)
                if not manual_journals:
                    return []

                for manual_journal in manual_journals:
                    if manual_journal.status == 'DRAFT':
                        manual_journal.status = 'DELETED'
                    elif manual_journal.status == 'POSTED':
                        manual_journal.status = 'VOIDED'

                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=manual_journals
                )

            return manual_journals_deleted

        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def get_organizations(self):
        """Retrieves Xero organization details.

        Scopes:
            accounting.settings
            accounting.settings.read

        Args:
            None.
        """
        organization_list = []
        
        try:
            api_response = self.accounting_api.get_organisations(
                self.tenant_id
            )
            organization_list = api_response.organisations
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return organization_list

    def get_payment(self, payment_id):
        """Retrieves a specific payment for invoices and credit notes using a unique payment Id.

        Scopes:
            accounting.settings
            accounting.settings.read

        Args:
            payment_id: Payment identifier.

        Returns:
            Dictionary of the specified payment.
        """
        payment = None
        
        try:
            api_response = self.accounting_api.get_payment(
                self.tenant_id,
                payment_id=payment_id
            )
            payment = api_response.payments[0]
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return payment

    def get_payments(self, **kwargs):
        """Retrieves payments for invoices and credit notes.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            if_modified_since: Items created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...
        """
        payment_list = []
        
        try:
            api_response = self.accounting_api.get_payments(
                self.tenant_id,
                **kwargs,
            )
            payment_list = api_response.payments
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return payment_list

    def create_payment(self, invoice_id, account_id, amount):
        """Creates a single payment for invoice or credit notes.

        Scopes:
            accounting.transactions

        Args:
        """
        invoice = Invoice(invoice_id=invoice_id)
        account = Account(account_id=account_id)
        date_value = date.today()

        payment = Payment(
            invoice=invoice,
            account=account,
            amount=amount,
            date=date_value)
        
        try:
            api_response = self.accounting_api.create_payment(
                self.tenant_id,
                payment
            )
            logger.debug(api_response)
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

    def create_payments():
        pass

    def get_repeating_invoice(self, repeating_invoice_id):
        """Retrieves a specific repeating invoice using a unique repeating invoice Id.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            repeating_invoice_id: RepeatingInvoice identifier.

        Returns:
            Dictionary of the specified repeating_invoice.
        """
        repeating_invoice = None
        
        try:
            api_response = self.accounting_api.get_repeating_invoice(
                self.tenant_id,
                repeating_invoice_id=repeating_invoice_id
            )
            repeating_invoice = api_response.repeating_invoices[0]
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return repeating_invoice

    def get_repeating_invoices(self, **kwargs):
        """Retrieves a list of repeating invoices that conform to the specified parameters.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...
        """
        repeating_invoice_list = []
        
        try:
            api_response = self.accounting_api.get_repeating_invoices(
                self.tenant_id,
                **kwargs
            )
            repeating_invoice_list = api_response.repeating_invoices
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return repeating_invoice_list
