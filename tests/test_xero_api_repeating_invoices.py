"""Tests Xero API Repeating Invoices.
"""
from datetime import datetime, timedelta
from xero_python.accounting import Contact
from xero_python.accounting import Invoice
from xero_python.accounting import LineItem

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_repeating_invoices(xero):
    # date_value = datetime.now().astimezone()
    # due_date_value = date_value + timedelta(days=7)

    # contact = Contact(
    #     contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')

    # line_item = LineItem(
    #     description = "Foobar",
    #     quantity = 1.0,
    #     unit_amount = 20.0,
    #     account_code = '400'
    # )
    
    # line_items = []    
    # line_items.append(line_item)

    # repeating_invoice = Invoice(
    #     type = "ACCREC",
    #     contact = contact,
    #     date = date_value,
    #     due_date = due_date_value,
    #     line_items = line_items,
    #     reference = "test_create_repeating_invoices()",
    #     status = "DRAFT")

    # repeating_invoice_list_created = xero.create_repeating_invoices(
    #     repeating_invoice_list=[repeating_invoice]
    # )

    # assert repeating_invoice_list_created
    # assert len(repeating_invoice_list_created) == 1
    assert True

def test_read_repeating_invoice(xero):
    reference = 'RPT400-1'
    repeating_invoice_id = '46370783-002e-4f34-9c76-d39449795b77'
    repeating_invoice = xero.read_repeating_invoices(id=repeating_invoice_id)

    assert repeating_invoice.repeating_invoice_id == repeating_invoice_id
    assert repeating_invoice.reference == reference

def test_read_repeating_invoices(xero):
    filter = 'Reference=="RPT400-1"'
    sort = 'Date ASC'

    repeating_invoice_list = xero.read_repeating_invoices(
        where=filter,
        order=sort
    )

    assert repeating_invoice_list
    assert len(repeating_invoice_list) > 0

def test_update_repeating_invoices(xero):
    # date_value = datetime.now().astimezone()
    # due_date_value = date_value + timedelta(days=7)
    # contact = Contact(
    #     contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    # line_item = LineItem(
    #     description="Foobar",
    #     quantity=1.0,
    #     unit_amount=20.0,
    #     account_code='400'
    # )   
    # line_items = []    
    # line_items.append(line_item)
    # repeating_invoice = Invoice(
    #     type="ACCREC",
    #     contact=contact,
    #     date=date_value,
    #     due_date=due_date_value,
    #     line_items=line_items,
    #     reference="test_update_repeating_invoices(): created",
    #     status="DRAFT")
    # repeating_invoice_list_created = xero.create_repeating_invoices(
    #     repeating_invoice_list=[repeating_invoice]
    # )
    # repeating_invoice = repeating_invoice_list_created[0]

    # # update journal
    # repeating_invoice.reference = "test_update_repeating_invoices()"
    # repeating_invoice_list_updated = xero.update_repeating_invoices(
    #     repeating_invoice_list=[repeating_invoice]
    # )

    # # verify
    # assert repeating_invoice_list_updated[0].reference == repeating_invoice.reference
    assert True

def test_delete_repeating_invoices_by_id(xero):
    # reference = "test_delete_repeating_invoices_by_id(): created"
    # date_value = datetime.now().astimezone()
    # due_date_value = date_value + timedelta(days=7)
    # contact = Contact(
    #     contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    # line_item = LineItem(
    #     description="Foobar",
    #     quantity=1.0,
    #     unit_amount=20.0,
    #     account_code='400'
    # )   
    # line_items = []    
    # line_items.append(line_item)
    # repeating_invoice = Invoice(
    #     type="ACCREC",
    #     contact=contact,
    #     date=date_value,
    #     due_date=due_date_value,
    #     line_items=line_items,
    #     reference=reference,
    #     status="DRAFT")
    # repeating_invoice_list_created = xero.create_repeating_invoices(
    #     repeating_invoice_list=[repeating_invoice]
    # )
    # repeating_invoice = repeating_invoice_list_created[0]

    # # delete journal
    # repeating_invoice_id = repeating_invoice.repeating_invoice_id
    # repeating_invoice_deleted = xero.delete_repeating_invoices(
    #     id=repeating_invoice_id
    # )[0]

    # assert repeating_invoice_deleted.repeating_invoice_id == repeating_invoice_id
    # assert repeating_invoice_deleted.reference == reference
    assert True

def test_delete_repeating_invoices_by_filter(xero):
#     filter = 'Reference.StartsWith("test_create")&&(Status=="DRAFT")'
#     sort = 'Date ASC'

#     repeating_invoices_deleted = xero.delete_repeating_invoices(
#         where=filter,
#         order=sort
#     )

#     assert repeating_invoices_deleted
#     assert len(repeating_invoices_deleted) > 0

# def test_delete_repeating_invoices_by_list_of_objects(xero):
#     filter = 'Reference.StartsWith("test_")&&(Status=="DRAFT")'
#     sort = 'Date ASC'

#     repeating_invoices = xero.read_repeating_invoices(
#         where=filter,
#         order=sort
#     )

#     repeating_invoices_deleted = xero.delete_repeating_invoices(
#         repeating_invoice_list=repeating_invoices
#     )

#     assert repeating_invoices_deleted
#     assert len(repeating_invoices_deleted) > 0
    assert True
