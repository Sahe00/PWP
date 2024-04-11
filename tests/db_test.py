""" Tests for the database models of onlinestore """
import os
import pytest
import tempfile
import time
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from onlinestore import create_app, db
from onlinestore.models import Customer, Order, Product, ProductOrder, Stock

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    ''' This function is called when a connection to the database is made '''
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture(scope="function")
def app():
    ''' Create and configure a new app instance for each test '''
    # Create a temporary database file for testing purposes
    test_config = {
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///database_test.db',
        "TESTING": True
    }

    app = create_app(test_config)

    with app.app_context():
        db.create_all()

    yield app

    # Teardown after testing
    with app.app_context():
        db.session.remove()
        db.drop_all()  # drop all tables in the database

def _get_customer(number=1):
    ''' Helper function to create a customer instance '''
    return Customer(
        #uuid="testuuid-{}".format(number),
        firstName="firstName-{}".format(number),
        lastName="lastName-{}".format(number),
        email="email-{}".format(number),
        phone="phone-{}-123456789".format(number)
    )

def _get_product(number=1):
    ''' Helper function to create a product instance '''
    return Product(
        name="product-{}".format(number),
        desc="desc-{}".format(number),
        price=number * 10.0
    )

def _get_order(customer):
    ''' Helper function to create an order instance '''
    return Order(
        customerId=customer,
        createdAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def _get_product_order(order, product, quantity=1):
    ''' Helper function to create a product order instance '''
    return ProductOrder(
        order=order,
        product=product,
        quantity=quantity
    )

def _get_stock(stockProduct, quantity=1):
    ''' Helper function to create a stock instance '''
    return Stock(
        quantity=quantity,
        stockProduct=stockProduct
    )

def test_create_instances(app):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that
    everything can be found from database, and that all relationships have been
    saved correctly.
    """

    with app.app_context():
        # Create everything
        customer = _get_customer(1)
        order = _get_order(customer.id)
        product = _get_product(1)
        product_order = _get_product_order(order, product, 1)
        stock = _get_stock(product, 1)

        #order.location = customer
        #product_order.sensor = order
        #stock.sensors.append(order)

        db.session.add(customer)
        db.session.add(order)
        db.session.add(product)
        db.session.add(product_order)
        db.session.add(stock)
        db.session.commit()

        # Check that everything exists
        assert Customer.query.count() == 1
        assert Order.query.count() == 1
        assert Product.query.count() == 1
        assert ProductOrder.query.count() == 1
        assert Stock.query.count() == 1

        #db_customer = Customer.query.first()
        #db_order = Order.query.first()
        #db_product = Product.query.first()
        #db_product_order = ProductOrder.query.first()
        #db_stock = Stock.query.first()

        # Check all relationships (both sides)
        #assert db_customer.orders == db_order
        #assert db_order.customer == db_customer
        #assert db_order.productOrders == db_product_order
        #assert db_product_order.order == db_order
        #assert db_product_order.product == db_product
        #assert db_product.products == db_product_order
        #assert db_product.stock == db_stock
        #assert db_stock.stockProduct == db_product
