from i_xero2 import XeroInterface

def test_init_xero():
	xero = XeroInterface()
	assert xero

	org = xero.get_organizations()[0]
	assert org.name == 'Demo Company (US)'
