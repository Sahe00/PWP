import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest

from onlinestore import db
from onlinestore.models import Stock
from onlinestore.utils import InventoryBuilder
from onlinestore.constants import *


class StockCollection(Resource):
    """
    StockCollection resource represents the collection of all products and their stock quantities.
    """
    # Retrieve all products and their stock quantities

    def get(self):
        body = InventoryBuilder()

        body.add_namespace("stock", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.stockcollection"))
        body.add_control_all_stock()  # GET
        body["items"] = []

        for stock in Stock.query.all():
            item = InventoryBuilder(stock.serialize())
            item.add_control("self", href=url_for("api.stockitem", product=stock.productId))
            item.add_control("profile", STOCK_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

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
        body = InventoryBuilder(product.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.stockitem", product=product.productId))
        body.add_control("profile", STOCK_PROFILE)
        body.add_control("collection", href=url_for("api.stockcollection"))
        body.add_control_get_product(product)  # GET product for the stock
        body.add_control_edit_stock(product)  # PUT
        body.add_control_delete_stock(product)  # DELETE

        return Response(json.dumps(body), 200, mimetype=MASON)

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

    # Delete stock quantity for product
    def delete(self, product):
        try:
            db.session.delete(product)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Product not found", 404
