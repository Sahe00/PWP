import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest

from flasgger import swag_from
from onlinestore import db
from onlinestore.models import Customer
from onlinestore.utils import InventoryBuilder
from onlinestore.constants import *


class CustomerCollection(Resource):
    # Returns a list of customers in the database
    @swag_from('../../doc/customer/customer_collection_get.yml')
    def get(self):
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.customercollection"))
        body.add_control_all_customers()  # GET
        body.add_control_add_customer()  # POST
        body["customers"] = []

        # List all customers in the database
        for customer in Customer.query.all():
            item = InventoryBuilder(customer.serialize())
            item.add_control("self", href=url_for("api.customeritem", customer=customer.uuid))
            item.add_control("profile", CUSTOMER_PROFILE)
            body["customers"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    # Creates a new customer to the database
    @swag_from('../../doc/customer/customer_collection_post.yml')
    def post(self):
        if not request.json:
            return "Unsupported media type", 415

        # Validate the JSON document against the schema
        try:
            validate(request.json, Customer.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))  # 400 Bad request

        email = request.json["email"]
        if db.session.query(Customer).filter(Customer.email == email).first():
            return "Customer with this email already exists", 409

        customer = Customer()
        customer.deserialize(request.json)

        try:
            db.session.add(customer)
            db.session.commit()
        except Exception as e:  # IntegrityError
            return f"Incomplete request - missing fields - {e}", 500

        return Response(status=201, headers={
            "Location": url_for("api.customeritem", customer=customer.uuid)
        })


class CustomerItem(Resource):
    # Returns a single customer from the database
    @swag_from('../../doc/customer/customer_item_get.yml')
    def get(self, customer):
        body = InventoryBuilder(customer.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.customeritem", customer=customer.uuid))
        body.add_control("profile", CUSTOMER_PROFILE)
        body.add_control("collection", href=url_for("api.customercollection"))
        body.add_control_edit_customer(customer)  # PUT
        body.add_control_delete_customer(customer)  # DELETE
        body["orders"] = []

        # List all orders for the customer
        for order in customer.orders:
            item = InventoryBuilder(order.serialize())
            item.add_control("self", href=url_for("api.orderitem", order=order.id))
            item.add_control("profile", ORDER_PROFILE)
            body["orders"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    # Updates a customer in the database
    @swag_from('../../doc/customer/customer_item_put.yml')
    def put(self, customer):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Customer.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))  # 400 Bad request

        # Check if customer email already exists
        email = request.json["email"]
        email_exists = db.session.query(Customer).filter(Customer.email == email).first()
        # If email is not the same as customers current email, check that it is unique
        if customer.email != email and email_exists:
            return "Customer with this email already exists", 409

        try:
            customer.deserialize(request.json)
            db.session.add(customer)
            db.session.commit()
        except IntegrityError:
            return "Database error", 500

        return Response(status=204)

    # Deletes a customer from the database
    @swag_from('../../doc/customer/customer_item_delete.yml')
    def delete(self, customer):
        db.session.delete(customer)
        db.session.commit()

        return Response(status=204)
