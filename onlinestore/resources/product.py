import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest

from onlinestore import db
from onlinestore.models import Product
from onlinestore.utils import InventoryBuilder
from onlinestore.constants import *


class ProductCollection(Resource):

    # Get list of all products (returns a Mason document)
    def get(self):
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.productcollection"))
        body.add_control_all_products()  # GET
        body.add_control_add_product()  # POST
        body["items"] = []

        for product in Product.query.all():
            item = InventoryBuilder(product.serialize())
            item.add_control("self", href=url_for("api.productitem", name=product.name))
            item.add_control("profile", PRODUCT_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

        # try:
        #    result = []
        #    for product in db.session.query(Product).all():
        #        p_info = {"name": "", "desc": "", "price": 0.0}
        #        p_info["name"] = product.name
        #        p_info["desc"] = product.desc
        #        p_info["price"] = product.price
        #        result.append(p_info)
        #    return result, 200
        # except Exception as e:
        #    return f"Error: {e}", 500

    # Creates a new product to the database
    def post(self):
        try:
            name = request.json["name"]
            if name is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, Product.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

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

                # Created
                return Response(status=201, headers={"Location": product_uri})
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


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
            validate(request.json, Product.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

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
