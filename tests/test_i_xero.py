"""Test functions to verify that the XeroInterface is working.

The tenant ID may change causing the authentication to fail. You can get the
tenant ID from the login UI and save it to the environment variables.
"""
from aracnid_logger import Logger
import pytest

from i_xero2 import ExpiredCredentialsException
from i_xero2 import XeroInterface

# initialize logging
logger = Logger(__name__).get_logger()


def test_init_xero():
    """Test xero initialization.
    """
    xero = XeroInterface()
    assert xero
    assert xero.client

    if xero.client:
        org = xero.read_organizations()[0]
        assert org.name == 'Demo Company (US)'

def test_init_xero_exception():
    """Test xero initialization, with invalid_grant.

    Need to manually put it in the state where the refresh token is expired.
    """
    with pytest.raises(ExpiredCredentialsException):
        xero = XeroInterface()
        assert xero
        assert xero.client

def test_init_xero_catch_exception():
    """Test xero initialization, with invalid_grant.

    Need to manually put it in the state where the refresh token is expired.
    """
    try:
        xero = XeroInterface()
        assert xero
        assert xero.client

    except ExpiredCredentialsException as err:
        assert err
