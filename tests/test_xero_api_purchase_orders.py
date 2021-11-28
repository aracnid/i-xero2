"""Tests Xero API PurchaseOrders.
"""
from datetime import datetime, date, timedelta
from xero_python.accounting import Contact
from xero_python.accounting import PurchaseOrder
from xero_python.accounting import LineItem

from i_xero2 import XeroInterface
import pytest

@pytest.fixture(name='xero')
def fixture_xero_interface():
    """Pytest fixture to initialize and return the XeroInterface object.
    """
    return XeroInterface()

def test_create_purchase_orders(xero):
    date_value = datetime.now().astimezone()

    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')

    line_item = LineItem(
        description = "Foobar",
        quantity = 1.0,
        unit_amount = 20.0,
        account_code = '000'
    )
    
    line_items = []    
    line_items.append(line_item)

    purchase_order = PurchaseOrder(
        contact = contact,
        date = date_value,
        line_items = line_items,
        reference = "test_create_purchase_orders()",
        status = "DRAFT")

    purchase_order_list_created = xero.create_purchase_orders(
        purchase_order_list=[purchase_order]
    )

    assert purchase_order_list_created
    assert len(purchase_order_list_created) == 1

def test_read_purchase_order_by_id(xero):
    purchase_order_number = 'PO-0001'
    purchase_order_id = '818032de-c60f-4bf6-98d5-b74df380e1d2'
    purchase_order = xero.read_purchase_orders(id=purchase_order_id)

    assert purchase_order.purchase_order_id == purchase_order_id
    assert purchase_order.purchase_order_number == purchase_order_number

def test_read_purchase_order_by_number(xero):
    purchase_order_number = 'PO-0001'
    purchase_order_id = '818032de-c60f-4bf6-98d5-b74df380e1d2'
    purchase_order = xero.read_purchase_orders(number=purchase_order_number)

    assert purchase_order.purchase_order_id == purchase_order_id
    assert purchase_order.purchase_order_number == purchase_order_number

def test_read_purchase_orders(xero):
    status = 'DRAFT'
    sort = 'Date ASC'

    purchase_order_list = xero.read_purchase_orders(
        status=status,
        order=sort
    )

    assert purchase_order_list
    assert len(purchase_order_list) > 0

def test_read_purchase_orders_by_date_range(xero):
    start = date.fromisoformat('2021-11-23')
    end = date.today()
    sort = 'Date ASC'

    purchase_order_list = xero.read_purchase_orders(
        date_from=start.isoformat(),
        date_to=end.isoformat(),
        order=sort
    )

    assert purchase_order_list
    assert len(purchase_order_list) > 0

def test_update_purchase_orders(xero):
    date_value = datetime.now().astimezone()
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    purchase_order = PurchaseOrder(
        contact=contact,
        date=date_value,
        line_items=line_items,
        reference="test_update_purchase_orders(): created",
        status="DRAFT")
    purchase_order_list_created = xero.create_purchase_orders(
        purchase_order_list=[purchase_order]
    )
    purchase_order = purchase_order_list_created[0]

    # update journal
    purchase_order.reference = "test_update_purchase_orders()"
    purchase_order_list_updated = xero.update_purchase_orders(
        purchase_order_list=[purchase_order]
    )

    # verify
    assert purchase_order_list_updated[0].reference == purchase_order.reference

def test_delete_purchase_orders_by_id(xero):
    reference = "test_delete_purchase_orders_by_id(): created"
    date_value = datetime.now().astimezone()
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    purchase_order = PurchaseOrder(
        contact=contact,
        date=date_value,
        line_items=line_items,
        reference=reference,
        status="DRAFT")
    purchase_order_list_created = xero.create_purchase_orders(
        purchase_order_list=[purchase_order]
    )
    purchase_order = purchase_order_list_created[0]

    # delete journal
    purchase_order_id = purchase_order.purchase_order_id
    purchase_order_deleted = xero.delete_purchase_orders(
        id=purchase_order_id
    )[0]

    assert purchase_order_deleted.purchase_order_id == purchase_order_id
    assert purchase_order_deleted.reference == reference

def test_delete_purchase_orders_by_filter(xero):
    date_value = datetime.now().astimezone()
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    purchase_order = PurchaseOrder(
        contact=contact,
        date=date_value,
        line_items=line_items,
        reference="test_delete_purchase_orders_by_filter(): created",
        status="DRAFT")
    purchase_order_list_created = xero.create_purchase_orders(
        purchase_order_list=[purchase_order]
    )
    purchase_order = purchase_order_list_created[0]

    start = date.today()
    sort = 'Date ASC'

    purchase_orders_deleted = xero.delete_purchase_orders(
        date_from=start.isoformat(),
        status='DRAFT',
        order=sort
    )

    assert purchase_orders_deleted
    assert len(purchase_orders_deleted) > 0

def test_delete_purchase_orders_by_list_of_objects(xero):
    date_value = datetime.now().astimezone()
    contact = Contact(
        contact_id = 'c7127731-d324-4e26-a03e-854ce9a3a269')
    line_item = LineItem(
        description="Foobar",
        quantity=1.0,
        unit_amount=20.0,
        account_code='400'
    )   
    line_items = []    
    line_items.append(line_item)
    purchase_order = PurchaseOrder(
        contact=contact,
        date=date_value,
        line_items=line_items,
        reference="test_delete_purchase_orders_by_list_of_objects(): created",
        status="DRAFT")
    purchase_order_list_created = xero.create_purchase_orders(
        purchase_order_list=[purchase_order]
    )
    purchase_order = purchase_order_list_created[0]

    start = date.today()
    sort = 'Date ASC'

    purchase_order_list = xero.read_purchase_orders(
        date_from=start.isoformat(),
        status='DRAFT',
        order=sort
    )

    purchase_orders_deleted = xero.delete_purchase_orders(
        purchase_order_list=purchase_order_list
    )

    assert purchase_orders_deleted
    assert len(purchase_orders_deleted) > 0
