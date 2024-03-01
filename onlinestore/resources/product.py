import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from onlinestore import db
from onlinestore.models import Customer, Order, ProductOrder, Product, Stock

from onlinestore.utils import ProductConverter

# /api/products/


class ProductCollection(Resource):

    # Retrieves all products from the database and forms a list of them
    def get(self):
        try:
            result = []
            for product in db.session.query(Product).all():
                p_info = {"name": "", "desc": "", "price": 0.0}
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
                return "Product already exists", 409
            try:
                product = Product()
                product.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                # product = Product(name=name, desc=desc, price=price)
                db.session.add(product)
                db.session.commit()

                product_uri = url_for("api.productcollection", name=product.name)

                return Response(status=201, headers={"Location": product_uri})  # Created
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


# /api/products/<name>
class ProductItem(Resource):

    # Retrieves information from a specific product
    def get(self, name):
        return name.serialize()

    # Deletes a product from the database
    def delete(self, name):
        try:
            db.session.delete(name)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Product not found", 404

    # Updates product information to the database
    def put(self, name):
        if not request.json:
            return "Unsupported media type", 415

        try:
            name.deserialize(request.json)
            db.session.add(name)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Product not found", 404
