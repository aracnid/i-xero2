"""Tests Xero API ManualJournals.
"""

from xero_python.accounting import ManualJournal
from xero_python.accounting import ManualJournalLine

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_manual_journals(xero):
    manual_journal_lines = []
    manual_journal_lines.append(ManualJournalLine(
        line_amount=100.0,
        account_code="600",
        description="Hello there"
    ))
    manual_journal_lines.append(ManualJournalLine(
        line_amount=-100.0,
        account_code="250",
        description="Hello there"
    ))
    manual_journal = ManualJournal(
        narration="Foobar",
        journal_lines=manual_journal_lines
    )

    manual_journal_list_created = xero.create_manual_journals(
        manual_journal_list=[manual_journal]
    )

    assert manual_journal_list_created
    assert len(manual_journal_list_created) == 1

def test_read_manual_journal(xero):
    narration = 'Coded incorrectly Office Equipment should be Computer Equipment'
    manual_journal_id = '7c02947d-d248-4875-a6a3-64ad98f98f16'
    manual_journal = xero.read_manual_journals(id=manual_journal_id)

    assert manual_journal.manual_journal_id == manual_journal_id
    assert manual_journal.narration == narration

def test_read_manual_journals(xero):
    filter = 'Status=="POSTED"'
    sort = 'Date ASC'

    manual_journal_list = xero.read_manual_journals(
        where=filter,
        order=sort
    )

    assert manual_journal_list
    assert len(manual_journal_list) == 1

def test_update_manual_journals(xero):
    # create new manual journal
    manual_journal_lines = []
    manual_journal_lines.append(ManualJournalLine(
        line_amount=100.0,
        account_code="600",
        description="Hello there"
    ))
    manual_journal_lines.append(ManualJournalLine(
        line_amount=-100.0,
        account_code="250",
        description="Hello there"
    ))
    manual_journal = ManualJournal(
        narration="Bar",
        journal_lines=manual_journal_lines
    )
    manual_journal_list_created = xero.create_manual_journals(
        manual_journal_list=[manual_journal]
    )
    manual_journal = manual_journal_list_created[0]

    # update journal
    manual_journal.narration = 'Foo'
    manual_journal_list_updated = xero.update_manual_journals(
        manual_journal_list=[manual_journal]
    )

    # verify
    assert manual_journal_list_updated[0].narration == manual_journal.narration

def test_delete_manual_journals_by_id(xero):
    # create new manual journal
    manual_journal_lines = []
    narration = 'Bar'
    manual_journal_lines.append(ManualJournalLine(
        line_amount=100.0,
        account_code="600",
        description="Hello there"
    ))
    manual_journal_lines.append(ManualJournalLine(
        line_amount=-100.0,
        account_code="250",
        description="Hello there"
    ))
    manual_journal = ManualJournal(
        narration=narration,
        journal_lines=manual_journal_lines
    )
    manual_journal_list_created = xero.create_manual_journals(
        manual_journal_list=[manual_journal]
    )
    manual_journal = manual_journal_list_created[0]

    # delete journal
    manual_journal_id = manual_journal.manual_journal_id
    manual_journal_deleted = xero.delete_manual_journals(
        id=manual_journal_id
    )[0]

    assert manual_journal_deleted.manual_journal_id == manual_journal_id
    assert manual_journal_deleted.narration == narration

def test_delete_manual_journals_by_filter(xero):
    filter = 'Narration.StartsWith("Foobar")&&(Status=="DRAFT"||Status=="Posted")'
    sort = 'Date ASC'

    manual_journal_list_deleted = xero.delete_manual_journals(
        where=filter,
        order=sort
    )

    assert manual_journal_list_deleted
    assert len(manual_journal_list_deleted) > 0

def test_delete_manual_journals_by_list_of_objects(xero):
    filter = 'Narration.StartsWith("Foo")&&(Status=="DRAFT"||Status=="Posted")'
    sort = 'Date ASC'

    manual_journals = xero.read_manual_journals(
        where=filter,
        order=sort
    )

    manual_journal_list_deleted = xero.delete_manual_journals(
        manual_journal_list=manual_journals
    )

    assert manual_journal_list_deleted
    assert len(manual_journal_list_deleted) > 0
