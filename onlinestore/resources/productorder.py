"""
This module defines the REST API for the ProductOrder resource. It handles
GET, POST, PUT, and DELETE requests for the ProductOrder resource.
"""
import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate

from flasgger import swag_from
from onlinestore import db
from onlinestore.models import ProductOrder, Order, Product
from onlinestore.utils import InventoryBuilder, create_error_response
from onlinestore.constants import *


class ProductOrderCollection(Resource):
    """ Resource ProductOrderCollection """

    @swag_from('../../doc/productorder/productorder_collection_get.yml')
    def get(self):
        ''' Get list of all product orders (returns a Mason document) '''
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.productordercollection"))
        body.add_control_all_productorders()  # GET
        body.add_control_add_productorder()  # POST
        body["productorders"] = []

        # List all product orders in the database
        for productorder in ProductOrder.query.all():
            item = InventoryBuilder(productorder.serialize())
            item.add_control("self", href=url_for(
                "api.productorderitem", productorder=productorder.id))
            item.add_control("profile", PRODUCTORDER_PROFILE)
            body["productorders"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/productorder/productorder_collection_post.yml')
    def post(self):
        ''' Create a new product order '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        # Validate the JSON document against the schema
        try:
            validate(request.json, ProductOrder.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        orderId = request.json["orderId"]
        if db.session.query(Order).filter(Order.id == orderId).first() is None:
            return create_error_response(
                404, "Not found",
                f"Order with ID {orderId} not found"
            )

        productId = request.json["productId"]
        if db.session.query(Product).filter(Product.id == productId).first() is None:
            return create_error_response(
                404, "Not found",
                f"Product with ID {productId} not found"
            )

        productOrder = ProductOrder()
        productOrder.deserialize(request.json)

        db.session.add(productOrder)
        db.session.commit()

        productOrder_uri = url_for("api.productordercollection", id=productOrder.id)
        return Response(status=201, headers={"Location": productOrder_uri})


class ProductOrderItem(Resource):
    """ Resource ProductOrderItem """

    @swag_from('../../doc/productorder/productorder_item_get.yml')
    def get(self, productorder):
        ''' Get product order details '''
        body = InventoryBuilder(productorder.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.productorderitem", productorder=productorder.id))
        body.add_control("profile", PRODUCTORDER_PROFILE)
        body.add_control("collection", href=url_for("api.productordercollection"))
        body.add_control_edit_productorder(productorder)  # PUT
        body.add_control_delete_productorder(productorder)  # DELETE

        # Get order and product details for the product order
        body.add_control_order(productorder)  # GET order details
        body.add_control_product(productorder)  # GET product details

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/productorder/productorder_item_put.yml')
    def put(self, productorder):
        ''' Update a product order '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, ProductOrder.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        productorder.deserialize(request.json)
        db.session.add(productorder)
        db.session.commit()

        return Response(status=204)

    @swag_from('../../doc/productorder/productorder_item_delete.yml')
    def delete(self, productorder):
        ''' Delete a product order '''
        db.session.delete(productorder)
        db.session.commit()

        return Response(status=204)
