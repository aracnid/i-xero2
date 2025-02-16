"""Tests Xero API Reports.
"""
from datetime import date

import pytest
import xero_python
import xero_python.accounting

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
    report = xero.read_report_balance_sheet(report_date=report_date)

    assert report
    assert isinstance(report, xero_python.accounting.models.report_with_row.ReportWithRow)
    assert report.report_id == 'BalanceSheet'
    assert report.rows[0].cells[1].value == '31 Jan 2025'

def test_read_balance_sheet_as_dict(xero):
    """Tests reading a balance sheet report as a dictionary.
    """
    report_date = date(2025, 1, 31)
    report = xero.read_report_balance_sheet(report_date=report_date, as_dict=True)

    assert report
    assert isinstance(report, dict)
    assert report['report_id'] == 'BalanceSheet'
    assert report['rows'][0]['cells'][1]['value'] == '31 Jan 2025'

def test_read_trial_balance(xero):
    """Tests reading a trial balance report.
    """
    report_date = date(2025, 1, 15)
    report = xero.read_report_trial_balance(report_date=report_date)

    assert report
    assert isinstance(report, xero_python.accounting.models.report_with_row.ReportWithRow)
    assert report.report_id == 'TrialBalance'
    assert report.report_titles[2] == 'As at 15 January 2025'

def test_read_trial_balance_as_dict(xero):
    """Tests reading a trial balance report as a dictionary.
    """
    report_date = date(2025, 1, 15)
    report = xero.read_report_trial_balance(report_date=report_date, as_dict=True)

    assert report
    assert isinstance(report, dict)
    assert report['report_id'] == 'TrialBalance'
    assert report['report_titles'][2] == 'As at 15 January 2025'
