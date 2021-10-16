from datetime import datetime, date

import dateutil
from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_payment(xero):
    assert False

def test_create_payments(xero):
    assert False

def test_get_invoice(xero):
    invoice_number = 'INV-0040'
    invoice_id = 'bad5068e-bf6a-4871-ac54-90d7b63f8dd1'
    invoice = xero.get_invoice(invoice_id)

    assert invoice.invoice_id == invoice_id
    assert invoice.invoice_number == invoice_number

def test_get_invoices_all(xero):
    invoice_list = xero.get_invoices()

    assert invoice_list
    assert len(invoice_list) == 77

def test_get_invoices_modified_since(xero):
    # The Demo Company doesn't initialize with any modification date
    # to the populated invoices.
    if_modified_since = datetime.fromisoformat('2021-10-12T00:00').astimezone()

    invoice_list = xero.get_invoices(
        if_modified_since=if_modified_since
    )

    assert invoice_list
    assert len(invoice_list) == 1

def test_get_invoices_by_filter(xero):
    filter = 'Reference=="Training"'
    sort = 'Date ASC'

    invoice_list = xero.get_invoices(
        where=filter,
        order=sort
    )

    assert invoice_list
    assert len(invoice_list) == 3

def test_get_invoices_by_invoice_numbers(xero):
    invoice_numbers = ['INV-0001', 'INV-0002']
    sort = 'Date ASC'

    invoice_list = xero.get_invoices(
        invoice_numbers=invoice_numbers,
        order=sort
    )

    assert invoice_list
    assert len(invoice_list) == 2

def test_get_item(xero):
    item_name = 'T-Shirt Large Black'
    item_id = '2f00bef1-5fe6-4d95-932d-99cd20f3bf45'
    item = xero.get_item(item_id)

    assert item.item_id == item_id
    assert item.name == item_name

def test_get_items_all(xero):
    item_list = xero.get_items()

    assert item_list
    assert len(item_list) == 11

def test_get_items_modified_since(xero):
    if_modified_since = datetime.fromisoformat('2021-10-12T00:00').astimezone()

    item_list = xero.get_items(
        if_modified_since=if_modified_since
    )

    assert item_list
    assert len(item_list) == 11

def test_get_items_by_filter(xero):
    filter = 'Code.StartsWith("TS")'
    sort = 'Name ASC'

    item_list = xero.get_items(
        where=filter,
        order=sort
    )

    assert item_list
    assert len(item_list) == 3

def test_get_organizations(xero):
    organization_list = xero.get_organizations()

    assert organization_list
    assert len(organization_list) == 1

def test_get_payment(xero):
    amount = 90.0
    payment_id = '2d173f02-90b0-4c30-bbe8-c83c2a4c8575'
    payment = xero.get_payment(payment_id)

    assert payment.payment_id == payment_id
    assert payment.amount == amount

def test_get_payments_all(xero):
    payment_list = xero.get_payments()

    assert payment_list
    assert len(payment_list) == 61

def test_get_payments_by_filter(xero):
    filter = 'Amount>90.0'
    sort = 'Date ASC'

    payment_list = xero.get_payments(
        where=filter,
        order=sort
    )

    assert payment_list
    assert len(payment_list) == 53

def test_get_repeating_invoice(xero):
    reference = 'RPT400-1'
    repeating_invoice_id = '46370783-002e-4f34-9c76-d39449795b77'
    repeating_invoice = xero.get_repeating_invoice(repeating_invoice_id)

    assert repeating_invoice.repeating_invoice_id == repeating_invoice_id
    assert repeating_invoice.reference == reference

def test_get_repeating_invoices_all(xero):
    repeating_invoice_list = xero.get_repeating_invoices()

    assert repeating_invoice_list
    assert len(repeating_invoice_list) == 6

def test_get_repeating_invoices_by_filter(xero):
    filter = 'Reference=="RPT400-1"'
    sort = 'Date ASC'

    repeating_invoice_list = xero.get_repeating_invoices(
        where=filter,
        order=sort
    )

    assert repeating_invoice_list
    assert len(repeating_invoice_list) == 1

def test_process_date(xero):
    payment_id = '2d173f02-90b0-4c30-bbe8-c83c2a4c8575'
    payment = xero.get_payment(payment_id)
    payment_date = payment.date

    assert type(payment_date) is date
