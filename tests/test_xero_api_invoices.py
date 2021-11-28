"""Tests Xero API Invoices.
"""
from datetime import datetime, date, timedelta
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

def test_create_invoices(xero):
    date_value = datetime.now().astimezone()
    due_date_value = date_value + timedelta(days=7)

    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')

    line_item = LineItem(
        description = "Foobar",
        quantity = 1.0,
        unit_amount = 20.0,
        account_code = '400'
    )
    
    line_items = []    
    line_items.append(line_item)

    invoice = Invoice(
        type = "ACCREC",
        contact = contact,
        date = date_value,
        due_date = due_date_value,
        line_items = line_items,
        reference = "test_create_invoices()",
        status = "DRAFT")

    invoice_list_created = xero.create_invoices(
        invoice_list=[invoice]
    )

    assert invoice_list_created
    assert len(invoice_list_created) == 1

def test_read_invoice(xero):
    invoice_number = 'INV-0024'
    invoice_id = '2bef3661-7cd8-496c-a31d-072a4dba8a79'
    invoice = xero.read_invoices(id=invoice_id)

    assert invoice.invoice_id == invoice_id
    assert invoice.invoice_number == invoice_number

def test_read_invoices(xero):
    filter = 'Status=="DRAFT"'
    sort = 'Date ASC'

    invoice_list = xero.read_invoices(
        where=filter,
        order=sort
    )

    assert invoice_list
    assert len(invoice_list) > 0

def test_read_invoices_by_date_range(xero):
    start = date.fromisoformat('2021-09-02')
    end = date.today()
    filter = (f'Date>={xero.xero_date_str(start)}'
        f'&&Date<{xero.xero_date_str(end)}')
    sort = 'Date ASC'

    invoice_list = xero.read_invoices(
        where=filter,
        order=sort
    )

    assert invoice_list
    assert len(invoice_list) > 0

def test_update_invoices(xero):
    date_value = datetime.now().astimezone()
    due_date_value = date_value + timedelta(days=7)
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    invoice = Invoice(
        type="ACCREC",
        contact=contact,
        date=date_value,
        due_date=due_date_value,
        line_items=line_items,
        reference="test_update_invoices(): created",
        status="DRAFT")
    invoice_list_created = xero.create_invoices(
        invoice_list=[invoice]
    )
    invoice = invoice_list_created[0]

    # update journal
    invoice.reference = "test_update_invoices()"
    invoice_list_updated = xero.update_invoices(
        invoice_list=[invoice]
    )

    # verify
    assert invoice_list_updated[0].reference == invoice.reference

def test_delete_invoices_by_id(xero):
    reference = "test_delete_invoices_by_id(): created"
    date_value = datetime.now().astimezone()
    due_date_value = date_value + timedelta(days=7)
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    invoice = Invoice(
        type="ACCREC",
        contact=contact,
        date=date_value,
        due_date=due_date_value,
        line_items=line_items,
        reference=reference,
        status="DRAFT")
    invoice_list_created = xero.create_invoices(
        invoice_list=[invoice]
    )
    invoice = invoice_list_created[0]

    # delete journal
    invoice_id = invoice.invoice_id
    invoice_deleted = xero.delete_invoices(
        id=invoice_id
    )[0]

    assert invoice_deleted.invoice_id == invoice_id
    assert invoice_deleted.reference == reference

def test_delete_invoices_by_filter(xero):
    filter = 'Reference.StartsWith("test_create")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    invoices_deleted = xero.delete_invoices(
        where=filter,
        order=sort
    )

    assert invoices_deleted
    assert len(invoices_deleted) > 0

def test_delete_invoices_by_list_of_objects(xero):
    filter = 'Reference.StartsWith("test_")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    invoices = xero.read_invoices(
        where=filter,
        order=sort
    )

    invoices_deleted = xero.delete_invoices(
        invoice_list=invoices
    )

    assert invoices_deleted
    assert len(invoices_deleted) > 0
