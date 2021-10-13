from i_xero import XeroInterface

def test_init_xero():
	xero = XeroInterface()
	assert xero

	org = xero.get_organizations()[0]
	assert org['Name'] == 'Lake Anne Brew House, LLC'
