"""Tests Xero API Repeating Invoices.
"""
from datetime import date, datetime, timedelta

from xero_python.accounting import Contact
from xero_python.accounting import RepeatingInvoice
from xero_python.accounting import LineItem
from xero_python.accounting import Schedule

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_repeating_invoices(xero):
    """Tests creating a repeating invoice.
    """
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

    # set the schedule
    start_date = date.today() + timedelta(days=7)
    schedule = Schedule(
        period=1,
        unit='WEEKLY',
        due_date=7,        
        due_date_type='DAYSAFTERBILLDATE',
        start_date=start_date,
        next_scheduled_date=start_date
    )

    repeating_invoice = RepeatingInvoice(
        type="ACCREC",
        contact=contact,
        schedule=schedule,
        line_items=line_items,
        reference="test_create_repeating_invoices()",
        status="DRAFT"
    )

    repeating_invoice_list_created = xero.create_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )

    assert repeating_invoice_list_created
    assert len(repeating_invoice_list_created) == 1
    # assert True

def test_read_repeating_invoice(xero):
    """Tests reading repeating invoice.
    """
    reference = 'RPT400-1'
    repeating_invoice_id = '46370783-002e-4f34-9c76-d39449795b77'
    repeating_invoice = xero.read_repeating_invoices(id=repeating_invoice_id)

    assert repeating_invoice.repeating_invoice_id == repeating_invoice_id
    assert repeating_invoice.reference == reference

def test_read_repeating_invoices(xero):
    """Tests reading multiple repeating invoices.
    """
    find_filter = 'Reference=="RPT400-1"'
    sort = 'Date ASC'

    repeating_invoice_list = xero.read_repeating_invoices(
        where=find_filter,
        order=sort
    )

    assert repeating_invoice_list
    assert len(repeating_invoice_list) > 0

@pytest.mark.xfail(reason='updating repeating invoices is not implemented')
def test_update_repeating_invoices(xero, caplog):
    """Tests updating repeating invoices.

    The "update" method is not implemented yet.
    """
    # region create repeating invoice
    reference = "test_update_repeating_invoices_by_id(): created"

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

    # set the schedule
    start_date = date.today() + timedelta(days=7)
    schedule = Schedule(
        period=1,
        unit='WEEKLY',
        due_date=7,        
        due_date_type='DAYSAFTERBILLDATE',
        start_date=start_date,
        next_scheduled_date=start_date
    )

    repeating_invoice = RepeatingInvoice(
        type="ACCREC",
        contact=contact,
        schedule=schedule,
        line_items=line_items,
        reference=reference,
        status="DRAFT"
    )

    repeating_invoice_list_created = xero.create_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )
    repeating_invoice = repeating_invoice_list_created[0]
    # endregion

    # update journal
    repeating_invoice.reference = "test_update_repeating_invoices()"

    repeating_invoice_list_updated = xero.update_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )

    # verify
    assert repeating_invoice_list_updated[0].reference == repeating_invoice.reference
    # assert caplog.messages[-1].startswith('AccountingBadRequestException')

def test_delete_repeating_invoices_by_id(xero):
    """Tests deleting repeating invoices by id.
    """
    # region create repeating invoice
    reference = "test_delete_repeating_invoices_by_id(): created"

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

    # set the schedule
    start_date = date.today() + timedelta(days=7)
    schedule = Schedule(
        period=1,
        unit='WEEKLY',
        due_date=7,        
        due_date_type='DAYSAFTERBILLDATE',
        start_date=start_date,
        next_scheduled_date=start_date
    )

    repeating_invoice = RepeatingInvoice(
        type="ACCREC",
        contact=contact,
        schedule=schedule,
        line_items=line_items,
        reference=reference,
        status="DRAFT"
    )

    repeating_invoice_list_created = xero.create_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )
    repeating_invoice = repeating_invoice_list_created[0]
    # endregion

    # delete repeating invoice
    repeating_invoice_id = repeating_invoice.repeating_invoice_id
    repeating_invoice_deleted = xero.delete_repeating_invoices(
        id=repeating_invoice_id
    )[0]

    assert repeating_invoice_deleted.repeating_invoice_id == repeating_invoice_id
    assert repeating_invoice_deleted.reference == reference

def test_delete_repeating_invoices_by_filter(xero):
    """Tests deleting repeating invoices by filter.
    """
    # region create repeating invoice
    reference = "test_delete_repeating_invoices_by_filter(): created"

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

    # set the schedule
    start_date = date.today() + timedelta(days=7)
    schedule = Schedule(
        period=1,
        unit='WEEKLY',
        due_date=7,        
        due_date_type='DAYSAFTERBILLDATE',
        start_date=start_date,
        next_scheduled_date=start_date
    )

    repeating_invoice = RepeatingInvoice(
        type="ACCREC",
        contact=contact,
        schedule=schedule,
        line_items=line_items,
        reference=reference,
        status="DRAFT"
    )

    repeating_invoice_list_created = xero.create_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )
    repeating_invoice = repeating_invoice_list_created[0]
    # endregion

    delete_filter = 'Reference.StartsWith("test_")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    repeating_invoices_deleted = xero.delete_repeating_invoices(
        where=delete_filter,
        order=sort
    )

    assert repeating_invoices_deleted
    assert len(repeating_invoices_deleted) > 0

def test_delete_repeating_invoices_by_list_of_objects(xero):
    """Tests deleting repeating invoices by list.
    """
    # region create repeating invoice
    reference = "test_delete_repeating_invoices_by_filter(): created"

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

    # set the schedule
    start_date = date.today() + timedelta(days=7)
    schedule = Schedule(
        period=1,
        unit='WEEKLY',
        due_date=7,        
        due_date_type='DAYSAFTERBILLDATE',
        start_date=start_date,
        next_scheduled_date=start_date
    )

    repeating_invoice = RepeatingInvoice(
        type="ACCREC",
        contact=contact,
        schedule=schedule,
        line_items=line_items,
        reference=reference,
        status="DRAFT"
    )

    repeating_invoice_list_created = xero.create_repeating_invoices(
        repeating_invoice_list=[repeating_invoice]
    )
    repeating_invoice = repeating_invoice_list_created[0]
    # endregion

    delete_filter = 'Reference.StartsWith("test_")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    repeating_invoices = xero.read_repeating_invoices(
        where=delete_filter,
        order=sort
    )

    repeating_invoices_deleted = xero.delete_repeating_invoices(
        repeating_invoice_list=repeating_invoices
    )

    assert repeating_invoices_deleted
    assert len(repeating_invoices_deleted) > 0
