import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock

class OrderCollection(Resource):

    # Returns a list of orders in the database
    def get(self):
        try:
            result = []
            for order in db.session.query(Order).all():
                o_info = {"customerId":"", "createdAt":""}
                o_info["customerId"] = order.customerId
                o_info["createdAt"] = order.createdAt
                result.append(o_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    def post(self):
        pass

    def delete(self):
        pass

    def put(self):
        pass

class OrderItem(Resource):
    def get(self):
        pass

    def post(self):
        pass

    def delete(self):
        pass

    def put(self):
        pass
