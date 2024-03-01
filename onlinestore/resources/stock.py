from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
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

    def post(self):
        try:
            productId = request.json["productId"]
            if productId is None:
                return "Request content type must be JSON", 415
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

    # Update stock quantity
    def put(self, product):
        if not request.json:
            return "Unsupported media type", 415

        try:
            product.deserialize(request.json)
            db.session.add(product)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Customer not found", 404