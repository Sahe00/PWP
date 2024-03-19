import json
import os
import uuid
from flask_sqlalchemy import SQLAlchemy
import pytest
import tempfile
import time
import createdatabase
from datetime import datetime
from flask.testing import FlaskClient
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from werkzeug.datastructures import Headers
from onlinestore import create_app, db
from onlinestore.models import Customer, Product, Order, ProductOrder, Stock


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# based on http://flask.pocoo.org/docs/1.0/testing/
# The fixture is invoked once for each test function that uses it
@pytest.fixture(scope="function")
def client():
    # Create a temporary database file for testing purposes
    test_config = {
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///temp.db',
        "TESTING": True
    }
    app = create_app(test_config)

    with app.app_context():
        createdatabase.create_test_db()
        client = app.test_client()

    yield client

    # Teardown after testing
    with app.app_context():
        db.session.remove()
        db.drop_all()  # drop all tables in the database


def _populate_db():
    for i in range(1, 4):
        customer = Customer(
            firstName="test-sensor-{}".format(i),
            lastName="testsensor",
            email="testEmail-{}".format(i),
            phone="testPhone-{}".format(i)
        )
        db.session.add(customer)

    # db_key = ApiKey(
    #    key=ApiKey.key_hash(TEST_KEY),
    #    admin=True
    # )
    # db.session.add(db_key)
    db.session.commit()


def _get_customer_json(number=1):
    """
    Creates a valid customer JSON object to be used for PUT and POST tests.
    """
    customer = {
        "firstName": "testName",
        "lastName": "testLastName",
        "email": "testemail@luukku.com",
        "phone": "04012345678"
    }
    return customer


def _get_product_json(number=1):
    """
    Creates a valid product JSON object to be used for PUT and POST tests.
    """
    product = {
        "name": "Sateenvarjo-2",
        "desc": "Sateenvarjo suojaa sinua sateelta kuin sateelta!",
        "price": 20.00
    }
    return product


class TestCustomerCollection(object):

    RESOURCE_URL = "/api/customers/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        for item in body:
            # firstName, lastName, email, phone
            assert len(item) == 5
            assert "firstName" in item
            assert "lastName" in item
            assert "email" in item
            assert "phone" in item

    def test_post(self, client):
        valid_json = _get_customer_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)  # Request content type must be JSON

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 201
        # assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid_json["name"] + "/")

        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409 (Already exists)
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 409

        # remove email field and try to post again, error 400 expected
        valid_json.pop("email")
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 400  # Invalid request body


class TestProductCollection(object):

    RESOURCE_URL = "/api/products/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        for item in body:
            # name, desc, price
            assert len(item) == 3
            assert "name" in item
            assert "desc" in item
            assert "price" in item

    def test_post(self, client):
        valid_json = _get_product_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)  # Request content type must be JSON

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 201
        # assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid_json["name"] + "/")

        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409 (Already exists)
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 409

        # remove required "name" field and try to post again, error 400 expected
        valid_json.pop("name")
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 400  # Invalid request body
