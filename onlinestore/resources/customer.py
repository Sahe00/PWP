import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock

class CustomerCollection(Resource):

    # Returns a list of customers in the database
    def get(self):
        try:
            result = []
            for product in db.session.query(Customer).all():
                c_info = {"firstName":"", "lastName":"", "email":"", "phone":""}
                c_info["firstName"] = product.firstName
                c_info["lastName"] = product.lastName
                c_info["email"] = product.email
                c_info["phone"] = product.phone
                result.append(c_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    def post(self):
        try:
            firstName = request.json["firstName"]
            if firstName is None:
                return "Request content type must be JSON", 415
            try:
                firstName = request.json["firstName"]
                lastName = request.json["lastName"]
                email = request.json["email"] # client will send as null if customer does not have an email
                if email == "":
                    email = None
                phone = request.json["phone"] # same with phone
                if phone == "":
                    phone = None
            except ValueError:
                return "Invalid request body", 400
            try:
                customer = Customer(firstName=firstName, lastName=lastName, email=email, phone=phone)
                db.session.add(customer)
                db.session.commit()
                print(customer.uuid) #TESTING
                print("haloo") #TESTING



                customer_uri = url_for("api.customercollection", uuid=customer.uuid)

                return Response(status=201, headers={"Location": customer_uri})
            except Exception as e: #IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class CustomerItem(Resource):
    def get(self, uuid):
        return uuid.serialize()

    def delete(self, uuid):
        try:
            # customer = db.session.query(Customer).filter(Customer.uuid == uuid).first()
            db.session.delete(uuid)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Customer not found", 404

    def put(self, uuid):
        if not request.json:
            return "Unsupported media type", 415

        try:
            customer = db.session.query(Customer).filter(Customer.uuid == uuid).first()

            #customer.firstName = request.json["firstName"]
            #customer.lastName = request.json["lastName"]
            #customer.email = request.json["email"]
            #customer.phone = request.json["phone"]

            # Update customer details
            customer.firstName = request.json.get("firstName", customer.firstName)
            customer.lastName = request.json.get("lastName", customer.lastName)
            customer.email = request.json.get("email", customer.email)
            customer.phone = request.json.get("phone", customer.phone)

            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Product not found", 404
