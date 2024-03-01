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
        pass

    def delete(self):
        pass


class StockItem(Resource):
    
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