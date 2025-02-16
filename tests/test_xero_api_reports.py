"""Tests Xero API Reports.
"""
from datetime import date

import pytest

from i_xero2 import XeroInterface

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_read_balance_sheet(xero):
    """Tests reading a balance sheet report.
    """
    report_date = date(2025, 1, 31)
    report = xero.read_report_balance_sheet(date=report_date)

    assert report
    assert report.report_id == 'BalanceSheet'
    assert report.rows[0].cells[1].value == '31 Jan 2025'
