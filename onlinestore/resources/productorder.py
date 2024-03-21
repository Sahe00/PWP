import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock


class ProductOrderCollection(Resource):
    def get(self):
        try:
            result = []
            for productOrder in db.session.query(ProductOrder).all():
                po_info = {"orderId": 0, "productId": 0, "quantity": 0}
                po_info["orderId"] = productOrder.orderId
                po_info["productId"] = productOrder.productId
                po_info["quantity"] = productOrder.quantity
                result.append(po_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    def post(self):
        try:
            orderId = request.json["orderId"]
            productId = request.json["productId"]
            if orderId is None or productId is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, ProductOrder.json_schema(),
                         format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

            if db.session.query(Order).filter(Order.id == orderId).first() is None:
                return f"Order with ID {orderId} not found", 404
            if db.session.query(Product).filter(Product.id == productId).first() is None:
                return f"Product with ID {productId} not found", 404
            try:
                productOrder = ProductOrder()
                productOrder.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                db.session.add(productOrder)
                db.session.commit()

                productOrder_uri = url_for("api.productordercollection", id=productOrder.id)

                return Response(status=201, headers={"Location": productOrder_uri})
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class ProductOrderItem(Resource):
    def get(self, productorder):
        return productorder.serialize(), 200

    def delete(self, productorder):
        try:
            db.session.delete(productorder)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Customer not found", 404

    def put(self, productorder):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, ProductOrder.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        try:
            productorder.deserialize(request.json)
            db.session.add(productorder)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Customer not found", 404
