""" Tests for the REST API resources. """
import json
# import os
# import uuid
# from flask_sqlalchemy import SQLAlchemy
from jsonschema import validate
import pytest
# import tempfile
# import time
import createdatabase
# from datetime import datetime
# from flask.testing import FlaskClient
from sqlalchemy.engine import Engine
from sqlalchemy import event
# from sqlalchemy.exc import IntegrityError, StatementError
from werkzeug.datastructures import Headers
from onlinestore import create_app, db
from onlinestore.models import Customer#, Product, Order, ProductOrder, Stock


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    ''' Enable foreign key support for SQLite '''
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# based on http://flask.pocoo.org/docs/1.0/testing/
# The fixture is invoked once for each test function that uses it
@pytest.fixture(scope="function")
def client():
    ''' Create a Flask test client for testing the API '''
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
    ''' Populate the database with test data '''
    for i in range(1, 4):
        customer = Customer(
            firstName=f"test-sensor-{i}",
            lastName="testsensor",
            email=f"testEmail-{i}",
            phone=f"testPhone-{i}"
        )
        db.session.add(customer)

    # db_key = ApiKey(
    #    key=ApiKey.key_hash(TEST_KEY),
    #    admin=True
    # )
    # db.session.add(db_key)
    db.session.commit()


def _check_namespace(client, response):
    """
    Checks that the "store" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"]["store"]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 200


def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200


def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


def _check_control_put_method(ctrl, client, obj, json_obj):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid object against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    validate(json_obj, schema)
    resp = client.put(href, json=json_obj)
    assert resp.status_code == 204


def _check_control_post_method(ctrl, client, obj, json_obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    validate(json_obj, schema)
    resp = client.post(href, json=json_obj)
    assert resp.status_code == 201


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


def _get_product_json(number=None):
    """
    Creates a valid product JSON object to be used for PUT and POST tests.
    """
    if number is None:
        name = "Sateenvarjo"
    else:
        name = "Sateenvarjo" + str(number)

    product = {
        "name": name,
        "desc": "Sateenvarjo suojaa sinua sateelta kuin sateelta!",
        "price": 20.00
    }
    return product


class TestCustomerCollection(object):
    """
    Tests for the CustomerCollection resource.
    """

    RESOURCE_URL = "/api/customers/"

    def test_get(self, client):
        ''' Test GET method for the CustomerCollection resource. '''
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        valid_json = _get_customer_json()
        _check_control_post_method("customer:add-customer", client, body, valid_json)
        assert len(body["customers"]) == 3
        for item in body["customers"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post(self, client):
        ''' Test POST method for the CustomerCollection resource. '''
        valid_json = _get_customer_json()

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)  # Bad request

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 201

        # Get customer uuid from the response header
        customer_uuid = resp.headers["Location"].split("/")[-2]

        # /api/customers/a3c7fea2-6a55-47b0-9f81-69d77798a61a/
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + customer_uuid + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409 (Already exists)
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 409

        # remove required "email" field and try to post again, error 400 expected
        valid_json.pop("email")
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 400  # Invalid request body


class TestCustomerItem(object):
    """
    Tests for the CustomerItem resource.
    """

    ALL_CUSTOMERS_URL = "/api/customers/"
    INVALID_URL = "/api/customers/non-customer-x/"

    def test_get(self, client):
        ''' Test GET method for the CustomerItem resource. '''
        resp = client.get(self.ALL_CUSTOMERS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first customer from the list
        CUSTOMER_URL = body["customers"][0]["@controls"]["self"]["href"]
        resp = client.get(CUSTOMER_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        valid_json = _get_customer_json()
        # Add missing uuid to the json object because it is generated in the models
        # uuid = ... default=lambda: str(uuid.uuid4()) ...
        valid_json["uuid"] = body["uuid"]
        _check_control_put_method("edit", client, body, valid_json)
        _check_control_delete_method("delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        ''' Test PUT method for the CustomerItem resource. '''
        valid_json = _get_customer_json()

        resp = client.get(self.ALL_CUSTOMERS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first customer from the list
        CUSTOMER_URL = body["customers"][0]["@controls"]["self"]["href"]

        # test with wrong content type
        resp = client.put(CUSTOMER_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        resp = client.put(self.INVALID_URL, json=valid_json)
        assert resp.status_code == 404  # Not found

        valid_customer_email = body["customers"][0].get("email")
        another_customer_email = body["customers"][1].get("email")

        # test with another customer's email
        valid_json["email"] = another_customer_email
        resp = client.put(CUSTOMER_URL, json=valid_json)
        assert resp.status_code == 409  # Conflict

        # test with valid email
        valid_json["email"] = valid_customer_email
        resp = client.put(CUSTOMER_URL, json=valid_json)
        assert resp.status_code == 204

        # remove email field for 400
        valid_json.pop("email")
        resp = client.put(CUSTOMER_URL, json=valid_json)
        assert resp.status_code == 400

    def test_delete(self, client):
        ''' Test DELETE method for the CustomerItem resource. '''
        resp = client.get(self.ALL_CUSTOMERS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first customer from the list
        CUSTOMER_URL = body["customers"][0]["@controls"]["self"]["href"]

        resp = client.delete(CUSTOMER_URL)
        assert resp.status_code == 204
        resp = client.delete(CUSTOMER_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestProductCollection(object):
    """
    Tests for the ProductCollection resource.
    """

    RESOURCE_URL = "/api/products/"

    def test_get(self, client):
        ''' Test GET method for the ProductCollection resource. '''
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        valid_json = _get_product_json(2)
        _check_control_post_method("product:add-product", client, body, valid_json)
        assert len(body["products"]) == 2
        for item in body["products"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    def test_post(self, client):
        ''' Test POST method for the ProductCollection resource. '''
        valid_json = _get_product_json(2)

        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data="notjson")
        # Request content type must be JSON
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 201

        # /api/products/Sateenvarjo-2/
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid_json["name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409 (Already exists)
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 409

        # remove required "name" field and try to post again, error 400 expected
        valid_json.pop("name")
        resp = client.post(self.RESOURCE_URL, json=valid_json)
        assert resp.status_code == 400  # Invalid request body


class TestProductItem(object):

    ALL_PRODUCTS_URL = "/api/products/"
    INVALID_URL = "/api/products/non-product-x/"

    def test_get(self, client):
        resp = client.get(self.ALL_PRODUCTS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first product from the list
        PRODUCT_URL = body["products"][0]["@controls"]["self"]["href"]
        resp = client.get(PRODUCT_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        valid_json = _get_product_json()
        _check_control_put_method("edit", client, body, valid_json)
        _check_control_delete_method("delete", client, body)
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        valid_json = _get_product_json()

        resp = client.get(self.ALL_PRODUCTS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first product from the list
        PRODUCT_URL = body["products"][0]["@controls"]["self"]["href"]

        # Test with wrong content type
        resp = client.put(PRODUCT_URL, data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # Test with invalid product URL
        resp = client.put(self.INVALID_URL, json=valid_json)
        assert resp.status_code == 404  # Not found

    def test_delete(self, client):
        resp = client.get(self.ALL_PRODUCTS_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)

        # Get url of first product from the list
        PRODUCT_URL = body["products"][0]["@controls"]["self"]["href"]

        resp = client.delete(PRODUCT_URL)
        assert resp.status_code == 204
        resp = client.delete(PRODUCT_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
