from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest
from onlinestore import db
from onlinestore.models import Stock


class StockCollection(Resource):

    # Retrieve all products and their stock quantities
    def get(self):
        try:
            result = []
            for stock in db.session.query(Stock).all():
                stock_info = {"productId": 0, "quantity": 0}
                stock_info["productId"] = stock.productId
                stock_info["quantity"] = stock.quantity
                result.append(stock_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    # TODO: Unnecessary method?
    def post(self):
        try:
            productId = request.json["productId"]
            if productId is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, Stock.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

            if db.session.query(Stock).filter(Stock.productId == productId).first():
                return "Product already exists", 409
            try:
                stock = Stock()
                Stock.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                db.session.add(stock)
                db.session.commit()

                stock_uri = url_for("api.stockitem", productId=stock.productId)

                return Response(status=201, headers={"Location": stock_uri})  # Created
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class StockItem(Resource):

    # Retrieve stock quantity for a specific product
    def get(self, product):
        return product.serialize(), 200

    # Update stock quantity for product
    def put(self, product):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Stock.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        if db.session.query(Stock).filter(Stock.productId == product.productId).first() is None:
            return f"Product with ID {product.productId} not found", 404

        # Ensure productId cannot be changed
        if 'productId' in request.json:
            return "Product ID cannot be modified", 400

        try:
            # product.deserialize(request.json)
            product.quantity = request.json["quantity"]
            db.session.add(product)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Product not found", 404
