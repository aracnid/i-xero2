"""Tests Xero API Contacts.
"""
from xero_python.accounting import Contact, Contacts

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_contacts(xero):
    contact = Contact(
        name = "Bruce Banner",
        email_address = "hulk@avengers.com"
    )

    contact_list_created = xero.create_contacts(
        contact_list=[contact]
    )

    assert contact_list_created
    assert len(contact_list_created) == 1

def test_read_contact(xero):
    assert False, 'not implemented'

    # item_name = 'T-Shirt Large Black'
    # item_id = '2f00bef1-5fe6-4d95-932d-99cd20f3bf45'
    # item = xero.read_items(id=item_id)

    # assert item.item_id == item_id
    # assert item.name == item_name

def test_read_contacts(xero):
    assert False, 'not implemented'

    # filter = 'Code.StartsWith("TS")'
    # sort = 'Name ASC'

    # item_list = xero.read_items(
    #     where=filter,
    #     order=sort
    # )

    # assert item_list
    # assert len(item_list) > 1

def test_update_contacts(xero):
    assert False, 'not implemented'

    # # create new item
    # item = Item(
    #     code="abcd",
    #     name="HelloWorld",
    #     description="Foobar",
    # )
    # item_list_created = xero.create_items(
    #     item_list=[item]
    # )
    # item = item_list_created[0]

    # # update journal
    # item.name = 'Foo'
    # item_list_updated = xero.update_items(
    #     item_list=[item]
    # )

    # # verify
    # assert item_list_updated[0].name == item.name

def test_delete_contacts_by_id(xero):
    assert False, 'not implemented'

    # # create new item
    # name = 'GoodbyeWorld'
    # item = Item(
    #     code="lmnop",
    #     name=name,
    #     description="Foobar"
    # )
    # item_list_created = xero.create_items(
    #     item_list=[item]
    # )
    # item = item_list_created[0]

    # # delete journal
    # item_id = item.item_id
    # xero.delete_items(id=item_id)

    # item_read = xero.read_items(id=item_id)
    # assert not item_read

def test_delete_contacts_by_filter(xero):
    assert False, 'not implemented'

    # filter = 'Name=="Foo"'
    # sort = 'UpdatedDateUTC ASC'

    # xero.delete_items(
    #     where=filter,
    #     order=sort
    # )

    # items_read = xero.read_items(where=filter)
    # assert not items_read

def test_delete_contacts_by_list_of_objects(xero):
    assert False, 'not implemented'

    # filter = 'Name.StartsWith("Hello")'
    # sort = 'UpdatedDateUTC ASC'

    # items = xero.read_items(
    #     where=filter,
    #     order=sort
    # )

    # xero.delete_items(
    #     item_list=items
    # )

    # items_read = xero.read_items(where=filter)
    # assert not items_read
