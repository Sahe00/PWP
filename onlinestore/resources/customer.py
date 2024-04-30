""" Customer resource module """
import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate

from flasgger import swag_from
from onlinestore import db
from onlinestore.models import Customer
from onlinestore.utils import InventoryBuilder, create_error_response
from onlinestore.constants import *


class CustomerCollection(Resource):
    """ Resource CustomerCollection """

    @swag_from('../../doc/customer/customer_collection_get.yml')
    def get(self):
        ''' Get list of all customers (returns a Mason document) '''
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

    @swag_from('../../doc/customer/customer_collection_post.yml')
    def post(self):
        ''' Create a new customer '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        # Validate the JSON document against the schema
        try:
            validate(request.json, Customer.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Check if customer email already exists
        email = request.json["email"]
        if db.session.query(Customer).filter(Customer.email == email).first():
            return create_error_response(
                409, "Already exists",
                "Customer with email '{}' already exists.".format(email)
            )

        customer = Customer()
        customer.deserialize(request.json)

        db.session.add(customer)
        db.session.commit()

        return Response(status=201, headers={
            "Location": url_for("api.customeritem", customer=customer.uuid)
        })


class CustomerItem(Resource):
    """ Resource CustomerItem """

    @swag_from('../../doc/customer/customer_item_get.yml')
    def get(self, customer):
        ''' Get a single customer from the database '''
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

    @swag_from('../../doc/customer/customer_item_put.yml')
    def put(self, customer):
        ''' Update a customer in the database '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Customer.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Check if customer email already exists
        email = request.json["email"]
        email_exists = db.session.query(Customer).filter(Customer.email == email).first()
        # If email is not the same as customers current email, check that it is unique
        if customer.email != email and email_exists:
            return create_error_response(
                409, "Already exists",
                "Customer with email '{}' already exists.".format(email)
            )

        customer.deserialize(request.json)
        db.session.add(customer)
        db.session.commit()

        return Response(status=204)

    @swag_from('../../doc/customer/customer_item_delete.yml')
    def delete(self, customer):
        ''' Delete a customer from the database '''
        db.session.delete(customer)
        db.session.commit()

        return Response(status=204)
