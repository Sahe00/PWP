import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock


class CustomerCollection(Resource):

    # Returns a list of customers in the database
    def get(self):
        try:
            result = []
            for customer in db.session.query(Customer).all():
                c_info = {"uuid": "", "firstName": "", "lastName": "", "email": "", "phone": ""}
                c_info["uuid"] = customer.uuid
                c_info["firstName"] = customer.firstName
                c_info["lastName"] = customer.lastName
                c_info["email"] = customer.email
                c_info["phone"] = customer.phone
                result.append(c_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

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

                customer_uri = url_for("api.customercollection", uuid=customer.uuid)

                return Response(status=201, headers={"Location": customer_uri})
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class CustomerItem(Resource):
    def get(self, customer):
        return customer.serialize()

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

            return Response(status=200)
        except IntegrityError:
            return "Customer not found", 404
