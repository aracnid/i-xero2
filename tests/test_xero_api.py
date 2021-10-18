from datetime import datetime, date

import dateutil
from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

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
