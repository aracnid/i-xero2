# import modules
from datetime import date
import os

from aracnid_logger import Logger
from i_mongodb import MongoDBInterface
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from pytz import timezone, utc
from xero_python.accounting import AccountingApi
from xero_python.accounting import Invoice, Invoices
from xero_python.accounting import Account, Payment
from xero_python.accounting import Items
from xero_python.accounting import ManualJournals
from xero_python.accounting import Payments, PaymentDelete
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.exceptions import AccountingBadRequestException
from xero_python.exceptions.http_status_exceptions import NotFoundException

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

    # INVOICES
    def create_invoices(self, invoice_list):
        """Creates one or more invoices.

        Scopes:
            accounting.transactions

        Args:
            invoice_list: List of invoices to create.

        Returns:
            List of created Invoice objects.
        """
        try:
            invoices = self.accounting_api.create_invoices(
                self.tenant_id,
                invoices=Invoices(invoices=invoice_list),
                unitdp=self.unitdp
            )
            return invoices.invoices
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def read_invoices(self, **kwargs):
        """Retrieves one or more invoices.

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
            Dictionary or list of retrieved invoices.
        """
        id = kwargs.pop('id', None)
        
        try:
            if id:
                invoices = self.accounting_api.get_invoice(
                    self.tenant_id,
                    invoice_id=id,
                    unitdp=self.unitdp
                )
                if len(invoices.invoices) == 1:
                    return invoices.invoices[0]
                else:
                    return None
            else:
                invoices = self.accounting_api.get_invoices(
                    self.tenant_id,
                    unitdp=self.unitdp,
                    **kwargs,
                )
                return invoices.invoices
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def update_invoices(self, invoice_list):
        """Updates one or more invoices.

        (Upsert) If an invoice does not exist it will be created.

        Scopes:
            accounting.transactions

        Args:
            invoice_list: List of invoices to update

        Returns:
            Dictionary or list of retrieved invoices.
        """
        try:
            invoices = self.accounting_api.update_or_create_invoices(
                self.tenant_id,
                invoices=Invoices(
                    invoices=invoice_list
                )
            )
            return invoices.invoices
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def delete_invoices(self, **kwargs):
        """Deletes/voids one or more invoices.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            invoice_list: List of Invoice objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted invoices.
        """
        id = kwargs.pop('id', None)
        invoice_list = kwargs.pop('invoice_list', None)

        try:
            if id:
                invoice = self.read_invoices(id=id)
                self.mark_invoice_deleted(invoice)
                invoices_deleted = self.update_invoices(
                    invoice_list=[invoice]
                )
            elif invoice_list:
                for invoice in invoice_list:
                    self.mark_invoice_deleted(invoice)
                invoices_deleted = self.update_invoices(
                    invoice_list=invoice_list
                )
            else:
                invoice_list_read = self.read_invoices(**kwargs)
                if not invoice_list_read:
                    return []

                for invoice in invoice_list_read:
                    self.mark_invoice_deleted(invoice)

                invoices_deleted = self.update_invoices(
                    invoice_list=invoice_list_read
                )

            return invoices_deleted

        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def mark_invoice_deleted(self, invoice):
        if invoice.status == 'DRAFT':
            invoice.status = 'DELETED'
        elif invoice.status == 'AUTHORISED':
            invoice.status = 'VOIDED'

    # ITEMS
    def create_items(self, item_list):
        """Creates one or more items.

        Scopes:
            accounting.settings

        Args:
            item_list: List of items to create.

        Returns:
            List of created Item objects.
        """
        try:
            items = self.accounting_api.create_items(
                self.tenant_id,
                items=Items(
                    items=item_list
                ),
                unitdp=self.unitdp
            )
            return items.items
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def read_items(self, **kwargs):
        """Retrieves one or more items.

        Scopes:
            accounting.settings
            accounting.settings.read

        Args:
            id: Identifier
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            Dictionary or list or retrieved items.
        """
        id = kwargs.pop('id', None)
        
        try:
            if id:
                items = self.accounting_api.get_item(
                    self.tenant_id,
                    item_id=id,
                    unitdp=self.unitdp
                )
                if len(items.items) == 1:
                    return items.items[0]
                else:
                    return None
            else:
                items = self.accounting_api.get_items(
                    self.tenant_id,
                    unitdp=self.unitdp,
                    **kwargs
                )
                return items.items
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')
        except NotFoundException as e:
            logger.error(f'Item not found: {id}')

        return []

    def update_items(self, item_list):
        """Updates one or more items.

        (Upsert) If a item does not exist it will be created.

        Scopes:
            accounting.transactions

        Args:
            item_list: List of items to update

        Returns:
            Dictionary or list of retrieved items.
        """
        try:
            items = self.accounting_api.update_or_create_items(
                self.tenant_id,
                items=Items(
                    items=item_list
                )
            )
            return items.items
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def delete_items(self, **kwargs):
        """Deletes/voids one or more items.

        Scopes:
            accounting.settings

        Args:
            id: Identifier
            item_list: List of Items objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted items.
        """
        id = kwargs.pop('id', None)
        item_list = kwargs.pop('item_list', None)

        try:
            if id:
                self.accounting_api.delete_item(
                    self.tenant_id,
                    item_id=id
                )
            elif item_list:
                for item in item_list:
                    self.accounting_api.delete_item(
                        self.tenant_id,                        
                        item_id=item.item_id
                    )
            else:
                item_list_read = self.read_items(**kwargs)
                if not item_list_read:
                    return []

                for item in item_list_read:
                    self.accounting_api.delete_item(
                        self.tenant_id,                        
                        item_id=item.item_id
                    )

        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

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
            manual_journal_list: List of ManualJournal objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted manual journals.
        """
        id = kwargs.pop('id', None)
        manual_journal_list = kwargs.pop('manual_journal_list', None)

        try:
            if id:
                manual_journal = self.read_manual_journals(id=id)
                self.mark_manual_journal_deleted(manual_journal)
                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=[manual_journal]
                )
            elif manual_journal_list:
                for manual_journal in manual_journal_list:
                    self.mark_manual_journal_deleted(manual_journal)
                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=manual_journal_list
                )
            else:
                manual_journal_list_read = self.read_manual_journals(**kwargs)
                if not manual_journal_list_read:
                    return []

                for manual_journal in manual_journal_list_read:
                    self.mark_manual_journal_deleted(manual_journal)

                manual_journals_deleted = self.update_manual_journals(
                    manual_journal_list=manual_journal_list_read
                )

            return manual_journals_deleted

        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def mark_manual_journal_deleted(self, manual_journal):
        if manual_journal.status == 'DRAFT':
            manual_journal.status = 'DELETED'
        elif manual_journal.status == 'POSTED':
            manual_journal.status = 'VOIDED'

    # ORGANIZATIONS
    def read_organizations(self, **kwargs):
        """Retrieves one or more manual journals.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Returns:
            List of retrieved organizations.
        """
        try:
            organizations = self.accounting_api.get_organizations(
                self.tenant_id
            )
            return organizations.organisations
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    # PAYMENTS
    def create_payments(self, payment_list):
        """Creates one or more payments.

        Scopes:
            accounting.transactions

        Args:
            payment_list: List of payments to create.

        Returns:
            List of created Payment objects.
        """
        try:
            payments = self.accounting_api.create_payments(
                self.tenant_id,
                payments=Payments(payments=payment_list)
            )
            return payments.payments
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def read_payments(self, **kwargs):
        """Retrieves one or more payments.

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
            Dictionary or list of retrieved payments.
        """
        id = kwargs.pop('id', None)
        
        try:
            if id:
                payments = self.accounting_api.get_payment(
                    self.tenant_id,
                    payment_id=id
                )
                if len(payments.payments) == 1:
                    return payments.payments[0]
                else:
                    return None
            else:
                payments = self.accounting_api.get_payments(
                    self.tenant_id,
                    **kwargs,
                )
                return payments.payments
        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

    def delete_payments(self, **kwargs):
        """Deletes/voids one or more payments.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            payment_list: List of Payment objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted payments.
        """
        id = kwargs.pop('id', None)
        payment_list = kwargs.pop('payment_list', None)

        try:
            if id:
                payment_delete = PaymentDelete(status = "DELETED")
                payments = self.accounting_api.delete_payment(
                    self.tenant_id,
                    payment_id=id,
                    payment_delete=payment_delete
                )
                return payments.payments

            elif payment_list:
                payment_delete = PaymentDelete(status = "DELETED")
                payment_list_deleted = []
                for payment in payment_list:
                    payments = self.accounting_api.delete_payment(
                        self.tenant_id,                        
                        payment_id=payment.payment_id,
                        payment_delete=payment_delete
                    )
                    payment_list_deleted.append(payments.payments[0])
                return payment_list_deleted

            else:
                payment_delete = PaymentDelete(status="DELETED")
                payment_list_read = self.read_payments(**kwargs)
                if not payment_list_read:
                    return []

                payment_list_deleted = []
                for payment in payment_list_read:
                    payments = self.accounting_api.delete_payment(
                        self.tenant_id,                        
                        payment_id=payment.payment_id,
                        payment_delete=payment_delete
                    )
                    payment_list_deleted.append(payments.payments[0])
                return payment_list_deleted

        except AccountingBadRequestException as e:
            logger.error(f'Exception: {e}\n')

        return []

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
