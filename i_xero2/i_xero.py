"""Class module to interface with Xero.
"""
# import modules
# pylint: disable=logging-fstring-interpolation,too-many-lines

from collections import deque
from datetime import date, datetime
import os
import time

from aracnid_logger import Logger
from i_mongodb import MongoDBInterface
from pytz import timezone, utc
from xero_python.accounting import AccountingApi
from xero_python.accounting import Contact, Contacts
from xero_python.accounting import CreditNotes
from xero_python.accounting import HistoryRecord, HistoryRecords
from xero_python.accounting import Invoices
from xero_python.accounting import Items
from xero_python.accounting import ManualJournals
from xero_python.accounting import Payments, PaymentDelete
from xero_python.accounting import PurchaseOrders
from xero_python.accounting import RepeatingInvoices
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.exceptions import AccountingBadRequestException
from xero_python.exceptions import HTTPStatusException
# from xero_python.exceptions import NotFoundException
from xero_python.exceptions.http_status_exceptions import NotFoundException

# initialize logging
logger = Logger(__name__).get_logger()


class ExpiredCredentialsException(Exception):
    """Exception: Credentials have expired.
    """
    def __init__(self):
        oauth2_url = os.environ.get('XERO_OAUTH2_URL')
        error_msg = f'NEED TO REAUTHORIZE XERO: {oauth2_url}'

        self.message = error_msg

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
            self.mdb = MongoDBInterface().get_mdb()

        # create credentials
        self.client_id = os.environ.get('XERO_CLIENT_ID')
        self.client_secret = os.environ.get('XERO_CLIENT_SECRET')
        self.scope_list = self.get_scopes()

        # set the xero client
        self.set_client()

        # if self.client:
        #     # set the APIs
        #     self.accounting_api = AccountingApi(self.client)

        # handle rate limit: 60 calls per minute
        self.rate_limit_calls = 60
        self.rate_limit_seconds = 60
        self.call_window = deque([], maxlen=self.rate_limit_calls)

        # track class instances
        XeroInterface.instances.append(self)
        logger.debug(f'XeroInterface.instances: {len(XeroInterface.instances)}')

    def throttle(self):
        """Records the call time and implements a delay to comply with rate limit.

        Rate limit is defined by self.rate_limit_calls and self.rate_limit_seconds.
        """
        # check for window length
        if len(self.call_window) < self.rate_limit_calls:
            self.call_window.append(datetime.now())
            return

        # check for window duration
        duration = (datetime.now() - self.call_window[0]).total_seconds()
        if duration < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - duration)
            self.call_window.append(datetime.now())

    def set_client(self):
        """Connect to Xero and set the client.
        """
        token = self.get_token()

        if token:
            logger.debug(f'[setup] expires: {token["expires_at"]}')
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
                try:
                    oauth2_token.refresh_access_token(self.client)

                except HTTPStatusException as err:
                    if err.status == 400 and 'invalid_grant' in str(err.body):
                        logger.warning('refresh_access_token: INVALID GRANT')
                        self.store_oauth2_token(None)
                        self.client = None
                        self.notify_to_reauthorize()
                        # raise(ExpiredCredentialsException)

                    else:
                        raise err

            # set the APIs
            if self.client:
                self.accounting_api = AccountingApi(self.client)

        else:
            self.client = None
            self.notify_to_reauthorize()
            # raise(ExpiredCredentialsException)

    def get_oauth2_token(self):
        """Retrieve the token.
        """
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
        """Save the token.

        Args:
            token: Token.
        """
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
        self.client.configuration.oauth2_token.update_token(**token)

        self.client.oauth2_token_saver(
            self.store_oauth2_token
        )(token)

    @staticmethod
    def notify_to_reauthorize():
        """Log the need to reauthorize Xero.
        """
        oauth2_url = os.environ.get('XERO_OAUTH2_URL')
        error_msg = f'NEED TO REAUTHORIZE XERO: {oauth2_url}'
        logger.error(error_msg)

        return error_msg

    def get_client(self):
        """Returns the Xero client.
        """
        return self.client

    def get_token(self):
        """Retrieve the token.
        """
        token = self.mdb.read_collection('xero_token').find_one(
            filter={'_id': 'token'}
        )

        # remove mongodb id
        if token:
            token.pop('_id')

        return token

    def save_token(self, token):
        """Save the specified token.

        Args:
            token: Token.
        """
        self.mdb.read_collection('xero_token').replace_one(
            filter={'_id': 'token'},
            replacement=token,
            upsert=True
        )

    def refresh_token(self):
        """Not working.
        """
        # token = self.credentials.token
        # # logger.debug(f'[refresh] token id: {token["id_token"]}')
        # logger.debug(f'[refresh] expires: {token["expires_at"]}')

        # self.credentials.refresh()
        # new_token = self.credentials.token
        # self.save_token(new_token)
        # logger.info('Refreshed Xero token')
        # logger.debug(f'[refresh] expires: {new_token["expires_at"]}')
        logger.debug('this function is not setup')

    def get_scopes(self):
        """Returns the Xero scopes as a list.
        """
        scopes = os.environ.get('XERO_SCOPES')
        scope_list = scopes.split(',')

        return scope_list

    @staticmethod
    def xero_date_str(date_or_datetime):
        """Converts a date or datetime object into a DateTime string.

        Args:
            date_or_datetime: A date or datetime object.
        """
        return f'DateTime({",".join([str(val) for val in date_or_datetime.timetuple()[:3]])})'

    @staticmethod
    def xero_datetime_str(date_or_datetime):
        """Converts a date or datetime object into a DateTime string.

        Args:
            date_or_datetime: A date or datetime object.
        """
        return f'DateTime({",".join([str(val) for val in date_or_datetime.timetuple()[:6]])})'

    @staticmethod
    def get_xero_datetime(dtx):
        """Returns the specified datetime in the local timezone.

        Args:
            dtx: Date-time.
        """
        est = timezone('US/Eastern')
        if dtx:
            if dtx.tzinfo:
                return dtx.astimezone(est)
            return est.localize(dtx)
        return None

    @staticmethod
    def get_xero_datetime_utc(dtx):
        """Returns the specified datetime in UTC.

        Args:
            dtx: Date-time.
        """
        if dtx:
            if dtx.tzinfo:
                return dtx.astimezone(utc)
            return utc.localize(dtx)
        return None

    # region ACCOUNTS
    def read_accounts(self, **kwargs):
        """Retrieves one or more accounts.

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
            Dictionary or list or retrieved accounts.
        """
        account_id = kwargs.pop('id', None)

        try:
            if account_id:
                self.throttle()
                accounts = self.accounting_api.get_account(
                    self.tenant_id,
                    account_id=account_id
                )
                if len(accounts.accounts) == 1:
                    return accounts.accounts[0]
                return None

            self.throttle()
            accounts = self.accounting_api.get_accounts(
                self.tenant_id,
                **kwargs
            )
            return accounts.accounts
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    # endregion

    # region CONTACTS
    def create_contacts(self, contact_list):
        """Creates one or more contacts.

        Scopes:
            accounting.settings

        Args:
            contact_list: List of contacts to create.

        Returns:
            List of created Contact objects.
        """
        # idempotency_key = 'KEY_VALUE'

        try:
            self.throttle()
            contacts = self.accounting_api.create_contacts(
                self.tenant_id,
                contacts=Contacts(
                    contacts=contact_list
                ),
                summarize_errors='True'
            )
            return contacts.contacts
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    # region CREDIT_NOTES
    def create_credit_notes(self, credit_note_list):
        """Creates one or more credit_notes.

        Scopes:
            accounting.transactions

        Args:
            credit_note_list: List of credit_notes to create.

        Returns:
            List of created Invoice objects.
        """
        try:
            self.throttle()
            credit_notes = self.accounting_api.create_credit_notes(
                self.tenant_id,
                credit_notes=CreditNotes(credit_notes=credit_note_list),
                unitdp=self.unitdp
            )
            return credit_notes.credit_notes
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def read_credit_notes(self, **kwargs):
        """Retrieves one or more credit_notes.

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
            Dictionary or list of retrieved credit_notes.
        """
        credit_note_id = kwargs.pop('id', None)

        try:
            if credit_note_id:
                self.throttle()
                credit_notes = self.accounting_api.get_credit_note(
                    self.tenant_id,
                    credit_note_id=credit_note_id,
                    unitdp=self.unitdp
                )
                if len(credit_notes.credit_notes) == 1:
                    return credit_notes.credit_notes[0]
                return None

            self.throttle()
            credit_notes = self.accounting_api.get_credit_notes(
                self.tenant_id,
                unitdp=self.unitdp,
                **kwargs,
            )
            return credit_notes.credit_notes
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def update_credit_notes(self, credit_note_list):
        """Updates one or more credit_notes.

        (Upsert) If an credit_note does not exist it will be created.

        Scopes:
            accounting.transactions

        Args:
            credit_note_list: List of credit_notes to update

        Returns:
            Dictionary or list of retrieved credit_notes.
        """
        try:
            self.throttle()
            credit_notes = self.accounting_api.update_or_create_credit_notes(
                self.tenant_id,
                credit_notes=CreditNotes(
                    credit_notes=credit_note_list
                )
            )
            return credit_notes.credit_notes
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def delete_credit_notes(self, **kwargs):
        """Deletes/voids one or more credit_notes.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            credit_note_list: List of Invoice objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted credit_notes.
        """
        credit_note_id = kwargs.pop('id', None)
        credit_note_list = kwargs.pop('credit_note_list', None)

        try:
            if credit_note_id:
                credit_note = self.read_credit_notes(id=credit_note_id)
                self.mark_credit_note_deleted(credit_note)
                credit_notes_deleted = self.update_credit_notes(
                    credit_note_list=[credit_note]
                )
            elif credit_note_list:
                for credit_note in credit_note_list:
                    self.mark_credit_note_deleted(credit_note)
                credit_notes_deleted = self.update_credit_notes(
                    credit_note_list=credit_note_list
                )
            else:
                credit_note_list_read = self.read_credit_notes(**kwargs)
                if not credit_note_list_read:
                    return []

                for credit_note in credit_note_list_read:
                    self.mark_credit_note_deleted(credit_note)

                credit_notes_deleted = self.update_credit_notes(
                    credit_note_list=credit_note_list_read
                )

            return credit_notes_deleted

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def mark_credit_note_deleted(self, credit_note):
        """Set the status of the credit note to 'deleted'.

        Args:
            credit_note: Xero credit note.
        """
        if credit_note.status == 'DRAFT':
            credit_note.status = 'DELETED'
        elif credit_note.status == 'AUTHORISED':
            credit_note.status = 'VOIDED'

    # endregion

    # region INVOICES
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
            self.throttle()
            invoices = self.accounting_api.create_invoices(
                self.tenant_id,
                invoices=Invoices(invoices=invoice_list),
                unitdp=self.unitdp
            )
            return invoices.invoices
        except AccountingBadRequestException as err:
            if err.reason == 'A Contact must be specified for this type of transaction':
                logger.error('Xero invoice creation failed: Missing contact')
            else:
                logger.error(f'Exception: {err}\n')

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
        invoice_id = kwargs.pop('id', None)

        try:
            if invoice_id:
                self.throttle()
                invoices = self.accounting_api.get_invoice(
                    self.tenant_id,
                    invoice_id=invoice_id,
                    unitdp=self.unitdp
                )
                if len(invoices.invoices) == 1:
                    return invoices.invoices[0]
                return None

            self.throttle()
            invoices = self.accounting_api.get_invoices(
                self.tenant_id,
                unitdp=self.unitdp,
                **kwargs,
            )
            return invoices.invoices
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
            self.throttle()
            invoices = self.accounting_api.update_or_create_invoices(
                self.tenant_id,
                invoices=Invoices(
                    invoices=invoice_list
                ),
                unitdp=self.unitdp
            )
            return invoices.invoices
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        invoice_id = kwargs.pop('id', None)
        invoice_list = kwargs.pop('invoice_list', None)

        try:
            if invoice_id:
                invoice = self.read_invoices(id=invoice_id)
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

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def mark_invoice_deleted(self, invoice):
        """Set the status of the invoice to 'deleted'.

        Args:
            invoice: Xero invoice.
        """
        if invoice.status == 'DRAFT':
            invoice.status = 'DELETED'
        elif invoice.status == 'AUTHORISED':
            invoice.status = 'VOIDED'

    def create_invoice_history(self, invoice_id: str, note: str) -> None:
        """Create an invoice history note.

        Args:
            invoice_id (str): Invoice identifier.
            note (str): The note to save to the invoice history.
        """
        history = self.accounting_api.create_invoice_history(
            self.tenant_id,
            invoice_id=invoice_id,
            history_records=HistoryRecords(
                history_records=[
                    HistoryRecord(details=note)
                ]
            ),
        )

        return history

    # endregion

    # region ITEMS
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
            self.throttle()
            items = self.accounting_api.create_items(
                self.tenant_id,
                items=Items(
                    items=item_list
                ),
                unitdp=self.unitdp
            )
            return items.items
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        item_id = kwargs.pop('id', None)

        try:
            if item_id:
                self.throttle()
                items = self.accounting_api.get_item(
                    self.tenant_id,
                    item_id=item_id,
                    unitdp=self.unitdp
                )
                if len(items.items) == 1:
                    return items.items[0]
                return None

            self.throttle()
            items = self.accounting_api.get_items(
                self.tenant_id,
                unitdp=self.unitdp,
                **kwargs
            )
            return items.items
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}')
        except NotFoundException:
            logger.error(f'Item not found: {item_id}')

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
            self.throttle()
            items = self.accounting_api.update_or_create_items(
                self.tenant_id,
                items=Items(
                    items=item_list
                )
            )
            return items.items
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        item_id = kwargs.pop('id', None)
        item_list = kwargs.pop('item_list', None)

        try:
            if item_id:
                self.throttle()
                self.accounting_api.delete_item(
                    self.tenant_id,
                    item_id=item_id
                )
            elif item_list:
                for item in item_list:
                    self.throttle()
                    self.accounting_api.delete_item(
                        self.tenant_id,
                        item_id=item.item_id
                    )
            else:
                item_list_read = self.read_items(**kwargs)
                if not item_list_read:
                    return []

                for item in item_list_read:
                    self.throttle()
                    self.accounting_api.delete_item(
                        self.tenant_id,
                        item_id=item.item_id
                    )

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    # endregion

    # region MANUAL_JOURNALS
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
            self.throttle()
            manual_journals = self.accounting_api.create_manual_journals(
                self.tenant_id,
                manual_journals=ManualJournals(
                    manual_journals=manual_journal_list
                )
            )
            return manual_journals.manual_journals
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        manual_journal_id = kwargs.pop('id', None)

        try:
            if manual_journal_id:
                self.throttle()
                manual_journals = self.accounting_api.get_manual_journal(
                    self.tenant_id,
                    manual_journal_id=manual_journal_id
                )
                if len(manual_journals.manual_journals) == 1:
                    return manual_journals.manual_journals[0]
                return None

            self.throttle()
            manual_journals = self.accounting_api.get_manual_journals(
                self.tenant_id,
                **kwargs,
            )
            return manual_journals.manual_journals
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
            self.throttle()
            manual_journals = self.accounting_api.update_or_create_manual_journals(
                self.tenant_id,
                manual_journals=ManualJournals(
                    manual_journals=manual_journal_list
                )
            )
            return manual_journals.manual_journals
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        manual_journal_id = kwargs.pop('id', None)
        manual_journal_list = kwargs.pop('manual_journal_list', None)

        try:
            if manual_journal_id:
                manual_journal = self.read_manual_journals(id=manual_journal_id)
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

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def mark_manual_journal_deleted(self, manual_journal):
        """Set the status of the manual journal to 'deleted'.

        Args:
            manual_journal: Xero manual journal.
        """
        if manual_journal.status == 'DRAFT':
            manual_journal.status = 'DELETED'
        elif manual_journal.status == 'POSTED':
            manual_journal.status = 'VOIDED'

    # endregion

    # region ORGANIZATIONS
    def read_organizations(self):
        """Retrieves a list of organizations.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Returns:
            List of retrieved organizations.
        """
        try:
            self.throttle()
            organizations = self.accounting_api.get_organisations(
                self.tenant_id
            )
            return organizations.organisations
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    # endregion

    # region PAYMENTS
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
            self.throttle()
            payments = self.accounting_api.create_payments(
                self.tenant_id,
                payments=Payments(payments=payment_list)
            )
            return payments.payments
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        payment_id = kwargs.pop('id', None)

        try:
            if payment_id:
                self.throttle()
                payments = self.accounting_api.get_payment(
                    self.tenant_id,
                    payment_id=payment_id
                )
                if len(payments.payments) == 1:
                    return payments.payments[0]
                return None

            self.throttle()
            payments = self.accounting_api.get_payments(
                self.tenant_id,
                **kwargs,
            )
            return payments.payments
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

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
        payment_id = kwargs.pop('id', None)
        payment_list = kwargs.pop('payment_list', None)

        try:
            if payment_id:
                payment_delete = PaymentDelete(status = "DELETED")
                self.throttle()
                payments = self.accounting_api.delete_payment(
                    self.tenant_id,
                    payment_id=payment_id,
                    payment_delete=payment_delete
                )
                return payments.payments

            if payment_list:
                payment_delete = PaymentDelete(status = "DELETED")
                payment_list_deleted = []
                for payment in payment_list:
                    self.throttle()
                    payments = self.accounting_api.delete_payment(
                        self.tenant_id,
                        payment_id=payment.payment_id,
                        payment_delete=payment_delete
                    )
                    payment_list_deleted.append(payments.payments[0])
                return payment_list_deleted

            payment_delete = PaymentDelete(status="DELETED")
            payment_list_read = self.read_payments(**kwargs)
            if not payment_list_read:
                return []

            payment_list_deleted = []
            for payment in payment_list_read:
                self.throttle()
                payments = self.accounting_api.delete_payment(
                    self.tenant_id,
                    payment_id=payment.payment_id,
                    payment_delete=payment_delete
                )
                payment_list_deleted.append(payments.payments[0])
            return payment_list_deleted

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    # endregion

    # region PURCHASE_ORDERS
    def create_purchase_orders(self, purchase_order_list):
        """Creates one or more purchase_orders.

        Scopes:
            accounting.transactions

        Args:
            purchase_order_list: List of purchase_orders to create.

        Returns:
            List of created Invoice objects.
        """
        try:
            self.throttle()
            purchase_orders = self.accounting_api.create_purchase_orders(
                self.tenant_id,
                purchase_orders=PurchaseOrders(purchase_orders=purchase_order_list)
            )
            return purchase_orders.purchase_orders
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def read_purchase_orders(self, **kwargs):
        """Retrieves one or more purchase_orders.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            id: Purchase Order identifier.
            number: Purchase Order number.
            if_modified_since: Created/modified since this datetime.
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            Dictionary or list of retrieved purchase_orders.
        """
        purchase_order_id = kwargs.pop('id', None)
        number = kwargs.pop('number', None)

        try:
            if purchase_order_id:
                self.throttle()
                purchase_orders = self.accounting_api.get_purchase_order(
                    self.tenant_id,
                    purchase_order_id=purchase_order_id
                )
                if len(purchase_orders.purchase_orders) == 1:
                    return purchase_orders.purchase_orders[0]
                return None

            if number:
                self.throttle()
                purchase_orders = self.accounting_api.get_purchase_order_by_number(
                    self.tenant_id,
                    purchase_order_number=number
                )
                if len(purchase_orders.purchase_orders) == 1:
                    return purchase_orders.purchase_orders[0]
                return None

            self.throttle()
            purchase_orders = self.accounting_api.get_purchase_orders(
                self.tenant_id,
                **kwargs,
            )
            return purchase_orders.purchase_orders
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        except NotFoundException:
            logger.info(f'purchase order not found: {number}, attempting indirect method')
            kwargs['number'] = number
            return self.read_purchase_orders_indirect(**kwargs)

        return []

    def read_purchase_orders_indirect(self, **kwargs):
        """Retrieves one or more purchase_orders.

        Scopes:
            accounting.transactions
            accounting.transactions.read

        Args:
            number: Purchase Order number.
            if_modified_since: Created/modified since this datetime.
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            Dictionary or list of retrieved purchase_orders.
        """
        number = kwargs.pop('number', None)

        try:
            if number:
                page = 1
                self.throttle()
                purchase_orders = self.accounting_api.get_purchase_orders(
                    self.tenant_id,
                    page=page,
                    **kwargs,
                )
                while len(purchase_orders.purchase_orders) > 0:
                    for purchase_order in purchase_orders.purchase_orders:
                        if purchase_order.purchase_order_number == number:
                            return purchase_order

                    # read next page
                    page += 1
                    self.throttle()
                    purchase_orders = self.accounting_api.get_purchase_orders(
                        self.tenant_id,
                        page=page,
                        **kwargs,
                    )

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def update_purchase_orders(self, purchase_order_list):
        """Updates one or more purchase_orders.

        (Upsert) If an purchase_order does not exist it will be created.

        Scopes:
            accounting.transactions

        Args:
            purchase_order_list: List of purchase_orders to update

        Returns:
            Dictionary or list of retrieved purchase_orders.
        """
        try:
            self.throttle()
            purchase_orders = self.accounting_api.update_or_create_purchase_orders(
                self.tenant_id,
                purchase_orders=PurchaseOrders(
                    purchase_orders=purchase_order_list
                )
            )
            return purchase_orders.purchase_orders
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def delete_purchase_orders(self, **kwargs):
        """Deletes/voids one or more purchase_orders.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            purchase_order_list: List of Invoice objects
            if_modified_since: Created/modified since this datetime.
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted purchase_orders.
        """
        purchase_order_id = kwargs.pop('id', None)
        purchase_order_list = kwargs.pop('purchase_order_list', None)

        try:
            if purchase_order_id:
                purchase_order = self.read_purchase_orders(id=purchase_order_id)
                self.mark_purchase_order_deleted(purchase_order)
                purchase_orders_deleted = self.update_purchase_orders(
                    purchase_order_list=[purchase_order]
                )
            elif purchase_order_list:
                for purchase_order in purchase_order_list:
                    self.mark_purchase_order_deleted(purchase_order)
                purchase_orders_deleted = self.update_purchase_orders(
                    purchase_order_list=purchase_order_list
                )
            else:
                purchase_order_list_read = self.read_purchase_orders(**kwargs)
                if not purchase_order_list_read:
                    return []

                for purchase_order in purchase_order_list_read:
                    self.mark_purchase_order_deleted(purchase_order)

                purchase_orders_deleted = self.update_purchase_orders(
                    purchase_order_list=purchase_order_list_read
                )

            return purchase_orders_deleted

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def mark_purchase_order_deleted(self, purchase_order):
        """Set the status of the purchase order to 'deleted'.

        Args:
            purchase_order: Xero purchase order.
        """
        if purchase_order.status == 'DRAFT':
            purchase_order.status = 'DELETED'
        elif purchase_order.status == 'AUTHORISED':
            purchase_order.status = 'DELETED'

    # endregion

    # region REPEATING_INVOICES
    def create_repeating_invoices(self, repeating_invoice_list):
        """Creates one or more repeating invoices.

        Scopes:
            accounting.transactions

        Args:
            repeating_invoice_list: List of repeating invoices to create.

        Returns:
            List of created RepeatingInvoice objects.
        """
        try:
            self.throttle()
            repeating_invoices = self.accounting_api.create_repeating_invoices(
                self.tenant_id,
                repeating_invoices=RepeatingInvoices(repeating_invoices=repeating_invoice_list)
            )
            return repeating_invoices.repeating_invoices
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def read_repeating_invoices(self, **kwargs):
        """Retrieves one or more repeating invoices.

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
            Dictionary or list of retrieved repeating invoices.
        """
        repeating_invoice_id = kwargs.pop('id', None)

        try:
            if repeating_invoice_id:
                self.throttle()
                repeating_invoices = self.accounting_api.get_repeating_invoice(
                    self.tenant_id,
                    repeating_invoice_id=repeating_invoice_id
                )
                if len(repeating_invoices.repeating_invoices) == 1:
                    return repeating_invoices.repeating_invoices[0]
                return None

            self.throttle()
            repeating_invoices = self.accounting_api.get_repeating_invoices(
                self.tenant_id,
                **kwargs
            )
            return repeating_invoices.repeating_invoices
        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def update_repeating_invoices(self, repeating_invoice_list):
        """Updates one or more repeating invoices.

        (Upsert) If a repeating invoice does not exist it will be created.

        NOTE: The "update" method only works to set the status to DELETED.

        Scopes:
            accounting.transactions

        Args:
            repeating_invoice_list: List of repeating invoices to update

        Returns:
            Dictionary or list of updated repeating invoices.
        """
        try:
            self.throttle()
            repeating_invoices = self.accounting_api.update_or_create_repeating_invoices(
                self.tenant_id,
                repeating_invoices=RepeatingInvoices(
                    repeating_invoices=repeating_invoice_list
                )
            )
            return repeating_invoices.repeating_invoices
        except AccountingBadRequestException as err:
            logger.error(f'AccountingBadRequestException: {err}\n')

        return []

    def delete_repeating_invoices(self, **kwargs):
        """Deletes/voids one or more repeating invoices.

        Scopes:
            accounting.transactions

        Args:
            id: Identifier
            repeating_invoice_list: List of RepeatingInvoice objects
            if_modified_since: Created/modified since this datetime.
            where: String to specify a filter
            order: String to specify a sort order, "<field> ASC|DESC"
            ...

        Returns:
            List of deleted repeating invoices.
        """
        repeating_invoice_id = kwargs.pop('id', None)
        repeating_invoice_list = kwargs.pop('repeating_invoice_list', None)

        try:
            if repeating_invoice_id:
                repeating_invoice = self.read_repeating_invoices(id=repeating_invoice_id)
                self.mark_repeating_invoice_deleted(repeating_invoice)
                repeating_invoices_deleted = self.update_repeating_invoices(
                    repeating_invoice_list=[repeating_invoice]
                )
            elif repeating_invoice_list:
                for repeating_invoice in repeating_invoice_list:
                    self.mark_repeating_invoice_deleted(repeating_invoice)
                repeating_invoices_deleted = self.update_repeating_invoices(
                    repeating_invoice_list=repeating_invoice_list
                )
            else:
                repeating_invoice_list_read = self.read_repeating_invoices(**kwargs)
                if not repeating_invoice_list_read:
                    return []

                for repeating_invoice in repeating_invoice_list_read:
                    self.mark_repeating_invoice_deleted(repeating_invoice)

                repeating_invoices_deleted = self.update_repeating_invoices(
                    repeating_invoice_list=repeating_invoice_list_read
                )

            return repeating_invoices_deleted

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}\n')

        return []

    def mark_repeating_invoice_deleted(self, repeating_invoice):
        """Set the status of the repeating invoice to 'deleted'.

        Args:
            repeating_invoice: Xero repeating invoice.
        """
        repeating_invoice.status = 'DELETED'

    # endregion

    # region REPORTS
    def read_report_balance_sheet(self, report_date: date, as_dict: bool=False) -> dict:
        """Retrieves a balance sheet report with the specified options.

        Scopes:
            accounting.reports.read
        
        Args:
            report_date (date): Date of the report.
            as_dict (bool): Return as dictionary or object.
            ...

        Returns:
            (dict) Report object.
        """
        try:
            if report_date:
                self.throttle()
                reports = self.accounting_api.get_report_balance_sheet(
                    self.tenant_id,
                    date=report_date,
                    standard_layout=True
                )
                report = reports.reports[0]
                if as_dict:
                    return report.to_dict()
                return report

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}')

        return None

    def read_report_trial_balance(self, report_date: date, as_dict: bool=False) -> dict:
        """Retrieves a trial balance report with the specified options.

        Scopes:
            accounting.reports.read
        
        Args:
            report_date (date): Date of the report.
            as_dict (bool): Return as dictionary or object.
            ...

        Returns:
            (dict) Report object.
        """
        try:
            if report_date:
                self.throttle()
                reports = self.accounting_api.get_report_trial_balance(
                    self.tenant_id,
                    date=report_date
                )
                report = reports.reports[0]
                if as_dict:
                    return report.to_dict()
                return report

        except AccountingBadRequestException as err:
            logger.error(f'Exception: {err}')

        return None

    # endregion
