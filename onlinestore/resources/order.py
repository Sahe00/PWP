from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock


class OrderCollection(Resource):

    # Returns a list of orders in the database
    def get(self):
        try:
            result = []
            for order in db.session.query(Order).all():
                o_info = {"customerId": "", "createdAt": ""}
                o_info["customerId"] = order.customerId
                o_info["createdAt"] = order.createdAt
                result.append(o_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    def post(self):
        try:
            customerId = request.json["customerId"]
            if customerId is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, Order.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

            if db.session.query(Customer).filter(Customer.id == customerId).first() is None:
                return f"Customer with ID {customerId} not found", 404
            try:
                order = Order()
                order.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                db.session.add(order)
                db.session.commit()

                order_uri = url_for("api.ordercollection", id=order.id)

                return Response(status=201, headers={"Location": order_uri})
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class OrderItem(Resource):
    def get(self, order):
        return order.serialize(), 200

    def delete(self, order):
        try:
            db.session.delete(order)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Customer not found", 404

    def put(self, order):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        try:
            order.deserialize(request.json)
            db.session.add(order)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Customer not found", 404
