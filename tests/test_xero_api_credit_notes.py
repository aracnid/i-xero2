"""Tests Xero API Credit Notes.

Credit notes for credit_notes are implemented (ACCRECCREDIT).
"""
from datetime import datetime, date, timedelta
from xero_python.accounting import Contact
from xero_python.accounting import CreditNote
from xero_python.accounting import LineItem

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_credit_notes(xero):
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

    credit_note = CreditNote(
        type = "ACCRECCREDIT",
        contact = contact,
        date = date_value,
        due_date = due_date_value,
        line_items = line_items,
        reference = "test_create_credit_notes()",
        status = "DRAFT")

    credit_note_list_created = xero.create_credit_notes(
        credit_note_list=[credit_note]
    )

    assert credit_note_list_created
    assert len(credit_note_list_created) == 1

def test_read_credit_note(xero):
    credit_note_number = 'CN-0026'
    credit_note_id = 'b5c13a5d-2723-4d15-8ff6-8848f4ce9756'
    credit_note = xero.read_credit_notes(id=credit_note_id)

    assert credit_note.credit_note_id == credit_note_id
    assert credit_note.credit_note_number == credit_note_number

def test_read_credit_notes(xero):
    filter = 'Status=="PAID"'
    sort = 'Date ASC'

    credit_note_list = xero.read_credit_notes(
        where=filter,
        order=sort
    )

    assert credit_note_list
    assert len(credit_note_list) > 0

def test_read_credit_notes_by_date_range(xero):
    start = date.fromisoformat('2021-09-02')
    end = date.today()
    filter = (f'Date>={xero.xero_date_str(start)}'
        f'&&Date<{xero.xero_date_str(end)}')
    sort = 'Date ASC'

    credit_note_list = xero.read_credit_notes(
        where=filter,
        order=sort
    )

    assert credit_note_list
    assert len(credit_note_list) > 0

def test_update_credit_notes(xero):
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
    credit_note = CreditNote(
        type="ACCRECCREDIT",
        contact=contact,
        date=date_value,
        due_date=due_date_value,
        line_items=line_items,
        reference="test_update_credit_notes(): created",
        status="DRAFT")
    credit_note_list_created = xero.create_credit_notes(
        credit_note_list=[credit_note]
    )
    credit_note = credit_note_list_created[0]

    # update journal
    credit_note.reference = "test_update_credit_notes()"
    credit_note_list_updated = xero.update_credit_notes(
        credit_note_list=[credit_note]
    )

    # verify
    assert credit_note_list_updated[0].reference == credit_note.reference

def test_delete_credit_notes_by_id(xero):
    reference = "test_delete_credit_notes_by_id(): created"
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
    credit_note = CreditNote(
        type="ACCRECCREDIT",
        contact=contact,
        date=date_value,
        due_date=due_date_value,
        line_items=line_items,
        reference=reference,
        status="DRAFT")
    credit_note_list_created = xero.create_credit_notes(
        credit_note_list=[credit_note]
    )
    credit_note = credit_note_list_created[0]

    # delete journal
    credit_note_id = credit_note.credit_note_id
    credit_note_deleted = xero.delete_credit_notes(
        id=credit_note_id
    )[0]

    assert credit_note_deleted.credit_note_id == credit_note_id
    assert credit_note_deleted.reference == reference

def test_delete_credit_notes_by_filter(xero):
    filter = 'Reference.StartsWith("test_create")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    credit_notes_deleted = xero.delete_credit_notes(
        where=filter,
        order=sort
    )

    assert credit_notes_deleted
    assert len(credit_notes_deleted) > 0

def test_delete_credit_notes_by_list_of_objects(xero):
    filter = 'Reference.StartsWith("test_")&&(Status=="DRAFT")'
    sort = 'Date ASC'

    credit_notes = xero.read_credit_notes(
        where=filter,
        order=sort
    )

    credit_notes_deleted = xero.delete_credit_notes(
        credit_note_list=credit_notes
    )

    assert credit_notes_deleted
    assert len(credit_notes_deleted) > 0
