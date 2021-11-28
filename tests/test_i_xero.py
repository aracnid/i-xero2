"""Test functions to verify that the XeroInterface is working.

The tenant ID may change causing the authentication to fail. You can get the 
tenant ID from the login UI and save it to the environment variables.
"""

from i_xero2 import XeroInterface

def test_init_xero():
	xero = XeroInterface()
	assert xero

	org = xero.read_organizations()[0]
	assert org.name == 'Demo Company (US)'
