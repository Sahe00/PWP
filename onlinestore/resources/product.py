import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock

class ProductCollection(Resource):

    # Retrieves all products from the database and forms a list of them
    def get(self):
        try:
            result = []
            for product in db.session.query(Product).all():
                p_info = {"name":"", "desc":"", "price":0.0}
                p_info["name"] = product.name
                p_info["desc"] = product.desc
                p_info["price"] = product.price
                result.append(p_info)
            return result, 200
        except Exception as e:
            return f"Error: {e}", 500

    # Creates a new product to the database
    def post(self):
        try:
            name = request.json["name"]
            if name is None:
                return "Request content type must be JSON", 415
            if db.session.query(Product).filter(Product.name == name).first():
                return "Name already exists", 409
            try:
                desc = request.json["desc"]
                price = float(request.json["price"])
            except ValueError:
                return "Invalid request body", 400

            try:
                product = Product(name=name, desc=desc, price=price)
                db.session.add(product)
                db.session.commit()

                product_uri = url_for("api.productitem", name=product.name)

                return Response(status=201, headers={"Location": product_uri})
            except IntegrityError:
                db.session.rollback()
                return "Incomplete request - missing fields", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400

    def delete(self):
        pass

    def put(self):
        pass

class ProductItem(Resource):
    def get(self, name):
        return Response(status=501)
