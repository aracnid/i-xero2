"""Tests Xero API Accounts.
"""
from xero_python.accounting import Account

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

# def test_create_accounts(xero):
#     account = Item(
#         code="abc",
#         name="HelloWorld",
#         description="Foobar",
#     )

#     account_list_created = xero.create_accounts(
#         account_list=[account]
#     )

#     assert account_list_created
#     assert len(account_list_created) == 1

def test_read_account(xero):
    account_name = 'Advertising'
    account_id = '2ec3335a-b20b-43b3-b6dc-40a5846936e2'
    account = xero.read_accounts(id=account_id)

    assert account.account_id == account_id
    assert account.name == account_name

def test_read_accounts(xero):
    filter = 'Code=="600"'
    sort = 'Name ASC'

    account_list = xero.read_accounts(
        where=filter,
        order=sort
    )

    assert account_list
    assert len(account_list) == 1

# def test_update_accounts(xero):
#     # create new account
#     account = Item(
#         code="abcd",
#         name="HelloWorld",
#         description="Foobar",
#     )
#     account_list_created = xero.create_accounts(
#         account_list=[account]
#     )
#     account = account_list_created[0]

#     # update journal
#     account.name = 'Foo'
#     account_list_updated = xero.update_accounts(
#         account_list=[account]
#     )

#     # verify
#     assert account_list_updated[0].name == account.name

# def test_delete_accounts_by_id(xero):
#     # create new account
#     name = 'GoodbyeWorld'
#     account = Item(
#         code="lmnop",
#         name=name,
#         description="Foobar"
#     )
#     account_list_created = xero.create_accounts(
#         account_list=[account]
#     )
#     account = account_list_created[0]

#     # delete journal
#     account_id = account.account_id
#     xero.delete_accounts(id=account_id)

#     account_read = xero.read_accounts(id=account_id)
#     assert not account_read

# def test_delete_accounts_by_filter(xero):
#     filter = 'Name=="Foo"'
#     sort = 'UpdatedDateUTC ASC'

#     xero.delete_accounts(
#         where=filter,
#         order=sort
#     )

#     accounts_read = xero.read_accounts(where=filter)
#     assert not accounts_read

# def test_delete_accounts_by_list_of_objects(xero):
#     filter = 'Name.StartsWith("Hello")'
#     sort = 'UpdatedDateUTC ASC'

#     accounts = xero.read_accounts(
#         where=filter,
#         order=sort
#     )

#     xero.delete_accounts(
#         account_list=accounts
#     )

#     accounts_read = xero.read_accounts(where=filter)
#     assert not accounts_read
