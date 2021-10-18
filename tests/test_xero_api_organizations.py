"""Tests Xero API Invoices.
"""
from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_read_organizations(xero):
    organization_list = xero.read_organizations()

    assert organization_list
    assert len(organization_list) > 0
