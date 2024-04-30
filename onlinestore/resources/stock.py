"""
This module defines the resources for the stock of products in the online store.
The StockCollection resource handles GET and POST requests for the stock of products.
The StockItem resource handles GET, PUT, and DELETE requests for a specific product's stock.
"""
import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate
from werkzeug.exceptions import BadRequest

from flasgger import swag_from
from onlinestore import db
from onlinestore.models import Stock, Product
from onlinestore.utils import InventoryBuilder, create_error_response
from onlinestore.constants import *


class StockCollection(Resource):
    """
    StockCollection resource represents the collection of all products and their stock quantities.
    """

    @swag_from('../../doc/stock/stock_collection_get.yml')
    def get(self):
        ''' Get list of all stock (returns a Mason document) '''
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.stockcollection"))
        body.add_control_all_stock()  # GET
        body["items"] = []

        for stock in Stock.query.all():
            item = InventoryBuilder(stock.serialize())
            item.add_control("self", href=url_for("api.stockitem", product=stock.productId))
            item.add_control("profile", STOCK_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/stock/stock_collection_post.yml')
    def post(self):
        ''' Create a new stock item '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        # Validate the JSON document against the schema
        try:
            validate(request.json, Stock.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Check if the entry already exists
        productId = request.json["productId"]
        if db.session.query(Stock).filter(Stock.productId == productId).first():
            return create_error_response(
                409, "Already exists",
                f"Stock entry for product with ID '{productId}' already exists."
            )
        # Check if the product exists
        if db.session.query(Product).filter(Product.id == productId).first() is None:
            return create_error_response(
                404, "Not found",
                f"Product with ID '{productId}' not found."
            )

        stock = Stock()
        stock.deserialize(request.json)

        db.session.add(stock)
        db.session.commit()

        stock_uri = url_for("api.stockitem", product=stock.productId)
        return Response(status=201, headers={"Location": stock_uri})  # Created


class StockItem(Resource):
    """ Resource StockItem """

    @swag_from('../../doc/stock/stock_item_get.yml')
    def get(self, product):
        ''' Get stock for a specific product (returns a Mason document) '''
        body = InventoryBuilder(product.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.stockitem", product=product.productId))
        body.add_control("profile", STOCK_PROFILE)
        body.add_control("collection", href=url_for("api.stockcollection"))
        body.add_control_get_product(product)  # GET product for the stock
        body.add_control_edit_stock(product)  # PUT
        body.add_control_delete_stock(product)  # DELETE

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/stock/stock_item_put.yml')
    def put(self, product):
        ''' Update stock quantity for product '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Stock.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Check if the product exists
        product_request_body = db.session.query(Product).filter(
            Product.id == request.json["productId"]).first()
        if product_request_body is None:
            return create_error_response(
                404, "Not found",
                f"Product with ID {request.json["productId"]} not found"
            )

        # Ensure productId is the same as the one in the URI, productId cannot be modified
        product = db.session.query(Stock).filter(Stock.productId == product.productId).first()
        if 'productId' in request.json and request.json['productId'] != product.productId:
            return create_error_response(
                400, "Invalid JSON document",
                "Product ID cannot be modified"
            )

        product.deserialize(request.json)
        db.session.add(product)
        db.session.commit()

        return Response(status=204)

    @swag_from('../../doc/stock/stock_item_delete.yml')
    def delete(self, product):
        ''' Delete a product's stock '''
        db.session.delete(product)
        db.session.commit()

        return Response(status=204)
