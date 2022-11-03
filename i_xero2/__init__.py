"""A set of functions to retrieve and save data into Xero.
"""
from importlib.metadata import version

from i_xero2.i_xero import ExpiredCredentialsException
from i_xero2.i_xero import XeroInterface
from i_xero2.i_xero_ui import XeroInterfaceUI


__version__ = version(__package__)
