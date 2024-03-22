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

                return Response(status=201, headers={
                    "Location": url_for("api.productitem", name=product.name)
                })
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class ProductItem(Resource):

    # Retrieves information from a specific product
    def get(self, name):
        body = InventoryBuilder(name.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.productitem", name=name.name))
        body.add_control("profile", PRODUCT_PROFILE)
        body.add_control("collection", href=url_for("api.productcollection"))
        body.add_control_edit_product(name)  # PUT
        body.add_control_delete_product(name)  # DELETE
        
        return Response(json.dumps(body), 200, mimetype=MASON)

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

            return Response(status=204)
        except IntegrityError:
            return "Product not found", 404
        
    # Deletes a product from the database
    def delete(self, name):
        try:
            db.session.delete(name)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Product not found", 404
