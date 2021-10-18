"""Tests Xero API Payments.
"""
from datetime import datetime, timedelta
from xero_python.accounting import Account
from xero_python.accounting import Contact
from xero_python.accounting import Invoice
from xero_python.accounting import LineItem
from xero_python.accounting import Payment

from i_xero2 import XeroInterface
import pytest


@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_payments(xero):
    date_value = datetime.now().astimezone()
    invoice = Invoice(invoice_id = "9eb7b996-4ac6-4cf8-8ee8-eb30d6e572e3")
    account = Account(account_id = "ceef66a5-a545-413b-9312-78a53caadbc4")
    payment = Payment(
        invoice=invoice,
        account=account,
        amount=10.0,
        date=date_value,
        reference='test_create_payments()'
    )

    payment_list_created = xero.create_payments(
        payment_list=[payment]
    )

    assert payment_list_created
    assert len(payment_list_created) == 1

def test_read_payment(xero):
    invoice_id = "9eb7b996-4ac6-4cf8-8ee8-eb30d6e572e3"
    invoice = xero.read_invoices(id=invoice_id)
    payment_list = invoice.payments
    payment_id = payment_list[0].payment_id
    payment = xero.read_payments(id=payment_id)

    assert payment.payment_id == payment_id
    assert payment.bank_amount == 10.0

def test_read_payments(xero):
    if_modified_since = datetime.fromisoformat('2021-01-01')
    sort = 'Date ASC'

    payment_list = xero.read_payments(
        if_modified_since=if_modified_since,
        order=sort
    )

    assert payment_list
    assert len(payment_list) > 0

# def test_read_payments_by_reference(xero):
#     filter = 'Reference.StartsWith("test_")'
#     sort = 'Date ASC'

#     payment_list = xero.read_payments(
#         where=filter,
#         order=sort
#     )

#     assert payment_list
#     assert len(payment_list) > 0

def test_delete_payments_by_id(xero):
    date_value = datetime.now().astimezone()
    invoice = Invoice(invoice_id = "9eb7b996-4ac6-4cf8-8ee8-eb30d6e572e3")
    account = Account(account_id = "ceef66a5-a545-413b-9312-78a53caadbc4")
    payment = Payment(
        invoice=invoice,
        account=account,
        amount=10.0,
        date=date_value,
        reference='test_delete_payments_by_id()'
    )
    payment_list_created = xero.create_payments(
        payment_list=[payment]
    )
    payment = payment_list_created[0]

    # delete journal
    payment_id = payment.payment_id
    xero.delete_payments(
        id=payment_id
    )

    payment_deleted = xero.read_payments(id=payment_id)
    assert payment_deleted
    assert payment_deleted.status == 'DELETED'

def test_delete_payments_by_filter(xero):
    amount = 10.0
    date_value = datetime.now().astimezone()
    invoice = Invoice(invoice_id = "9eb7b996-4ac6-4cf8-8ee8-eb30d6e572e3")
    account = Account(account_id = "ceef66a5-a545-413b-9312-78a53caadbc4")
    payment = Payment(
        invoice=invoice,
        account=account,
        amount=amount,
        date=date_value,
        reference='test_delete_payments_by_filter()'
    )
    payment_list_created = xero.create_payments(
        payment_list=[payment]
    )

    filter = 'Amount==10.0&&Status=="AUTHORISED"'
    sort = 'Date ASC'

    xero.delete_payments(
        where=filter,
        order=sort
    )

    payment_list_deleted = xero.read_payments(
        # where='Amount==10.0&&Status=="DELETED"'
        where='Amount==10.0'
    )

    assert payment_list_deleted
    assert len(payment_list_deleted) > 0
    for payment_deleted in payment_list_deleted:
        assert payment_deleted.status == 'DELETED'

def test_delete_payments_by_list_of_objects(xero):
    reference = 'test_delete_payments_by_list_of_objects()'
    date_value = datetime.now().astimezone()
    invoice = Invoice(invoice_id = "9eb7b996-4ac6-4cf8-8ee8-eb30d6e572e3")
    account = Account(account_id = "ceef66a5-a545-413b-9312-78a53caadbc4")
    payment = Payment(
        invoice=invoice,
        account=account,
        amount=10.0,
        date=date_value,
        reference=reference
    )
    payment_list_created = xero.create_payments(
        payment_list=[payment]
    )

    filter = 'Amount==10.0&&Status=="AUTHORISED"'
    sort = 'Date ASC'

    payment_list = xero.read_payments(
        where=filter,
        order=sort
    )

    payment_list_deleted = xero.delete_payments(
        payment_list=payment_list
    )

    # payment_list_deleted = xero.read_payments(
    #     where='Reference.StartsWith("test_")'
    # )

    assert payment_list_deleted
    assert len(payment_list_deleted) > 0
    for payment_deleted in payment_list_deleted:
        assert payment_deleted.status == 'DELETED'
