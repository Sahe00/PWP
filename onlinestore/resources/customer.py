import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest

from onlinestore import db
from onlinestore.models import Customer
from onlinestore.utils import InventoryBuilder
from onlinestore.constants import *


class CustomerCollection(Resource):

    # Returns a list of customers in the database
    def get(self):
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.customercollection"))
        body.add_control_all_customers()  # GET
        body.add_control_add_customer()  # POST
        body["items"] = []

        for customer in Customer.query.all():
            item = InventoryBuilder(customer.serialize())
            item.add_control("self", href=url_for("api.customeritem", customer=customer.uuid))
            item.add_control("profile", CUSTOMER_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    # Creates a new customer to the database
    def post(self):
        try:
            email = request.json["email"]
            if email is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, Customer.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

            if db.session.query(Customer).filter(Customer.email == email).first():
                return "Customer with this email already exists", 409
            try:
                customer = Customer()
                customer.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                db.session.add(customer)
                db.session.commit()
            
                return Response(status=201, headers={
                    "Location": url_for("api.customeritem", customer=customer.uuid)
                })
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class CustomerItem(Resource):
    def get(self, customer):
        body = InventoryBuilder(customer.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.customeritem", customer=customer.uuid))
        body.add_control("profile", CUSTOMER_PROFILE)
        body.add_control("collection", href=url_for("api.customercollection"))
        body.add_control_edit_customer(customer)  # PUT
        body.add_control_delete_customer(customer)  # DELETE
        
        return Response(json.dumps(body), 200, mimetype=MASON)

    def delete(self, customer):
        try:
            db.session.delete(customer)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Customer not found", 404

    def put(self, customer):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Customer.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        try:
            customer.deserialize(request.json)
            db.session.add(customer)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=204)
        except IntegrityError:
            return "Customer not found", 404
