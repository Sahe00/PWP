"""This module defines the resources for the Order and OrderCollection endpoints."""
import json
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, validate

from flasgger import swag_from
from onlinestore import db
from onlinestore.models import Order, Customer
from onlinestore.utils import InventoryBuilder, create_error_response
from onlinestore.constants import *


class OrderCollection(Resource):
    """Resource OrderCollection"""

    @swag_from('../../doc/order/order_collection_get.yml')
    def get(self):
        ''' Get list of all orders (returns a Mason document) '''
        body = InventoryBuilder()

        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.ordercollection"))
        body.add_control_all_orders()  # GET
        body.add_control_add_order()  # POST
        body["orders"] = []

        # List all orders in the database
        for order in Order.query.all():
            item = InventoryBuilder(order.serialize())
            item.add_control("self", href=url_for("api.orderitem", order=str(order.id)))
            item.add_control("profile", ORDER_PROFILE)
            body["orders"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/order/order_collection_post.yml')
    def post(self):
        ''' Create a new order '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        # Validate the JSON document against the schema
        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        # Check if the customer exists
        customerId = request.json["customerId"]
        if db.session.query(Customer).filter(Customer.id == customerId).first() is None:
            return create_error_response(
                404, "Not found",
                "Customer with id '{}' not found.".format(customerId)
            )

        order = Order()
        order.deserialize(request.json)

        db.session.add(order)
        db.session.commit()

        order_uri = url_for("api.orderitem", order=order.id)
        return Response(status=201, headers={"Location": order_uri})


class OrderItem(Resource):
    """Resource OrderItem"""

    @swag_from('../../doc/order/order_item_get.yml')
    def get(self, order):
        ''' Get order details '''
        body = InventoryBuilder(order.serialize())
        body.add_namespace("store", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for("api.orderitem", order=str(order.id)))
        body.add_control("profile", ORDER_PROFILE)
        body.add_control("collection", href=url_for("api.ordercollection"))
        body.add_control_customer_to_order(order)  # GET customer to order
        body.add_control_edit_order(order)  # PUT
        body.add_control_delete_order(order)  # DELETE
        body["productorders"] = []

        # List all product orders for the order
        for product_order in order.productOrders:
            item = InventoryBuilder(product_order.serialize())
            href = url_for("api.productorderitem", productorder=product_order.id)
            item.add_control("self", href=href)
            item.add_control("profile", PRODUCTORDER_PROFILE)
            body["productorders"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    @swag_from('../../doc/order/order_item_put.yml')
    def put(self, order):
        ''' Update an order '''
        if request.content_type != JSON:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Order.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        order.deserialize(request.json)
        db.session.add(order)
        db.session.commit()

        return Response(status=204)

    @swag_from('../../doc/order/order_item_delete.yml')
    def delete(self, order):
        ''' Delete an order '''
        db.session.delete(order)
        db.session.commit()

        return Response(status=204)
