'''
Utility methods for onlinestore API
'''
import json
from flask import Response, request, url_for
from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound

from onlinestore.models import *
from onlinestore.constants import *


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        # TODO: Change name prefix to store:edit?
        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        # TODO: Change name prefix to store:delete?
        self.add_control(
            "delete",
            href,
            method="DELETE",
            title=title,
        )


class InventoryBuilder(MasonBuilder):
    """
    A subclass of MasonBuilder that adds some convenience methods for
    constructing Mason objects that are specific to the store inventory
    application. This class is not generic and contains application specific
    implementation details.
    """

    def add_control_all_products(self):
        ''' Add control to get all products '''
        self.add_control(
            "product:get-products",
            url_for("api.productcollection"),
            method="GET",
            title="Get all products",
        )

    def add_control_all_customers(self):
        ''' Add control to get all customers '''
        self.add_control(
            "customer:get-customers",
            url_for("api.customercollection"),
            method="GET",
            title="Get all customers",
        )

    def add_control_all_orders(self):
        ''' Add control to get all orders '''
        self.add_control(
            "order:get-orders",
            url_for("api.ordercollection"),
            method="GET",
            title="Get all orders",
        )

    def add_control_all_productorders(self):
        ''' Add control to get all product orders '''
        self.add_control(
            "productorder:get-productorders",
            url_for("api.productordercollection"),
            method="GET",
            title="Get all product orders",
        )

    def add_control_all_stock(self):
        ''' Add control to get all stock '''
        self.add_control(
            "stock:get-stocks",
            url_for("api.stockcollection"),
            method="GET",
            title="Get all stocks",
        )

    def add_control_customer_to_order(self, order):
        ''' Add control to get customer to order '''
        self.add_control(
            "order:by-customer",
            url_for("api.customeritem", customer=order.customer.uuid),
            method="GET",
            title="Get customer to order",
        )

    def add_control_customer_orders(self, customer):
        ''' Add control to get customer orders '''
        self.add_control(
            "customer:customer-orders",
            url_for("api.orderitem", order=customer.uuid),
            method="GET",
            title="Get customer orders",
        )

    def add_control_get_productorder(self, product):
        ''' Add control to get product order '''
        self.add_control(
            "product:get-productorder",
            url_for("api.productorderitem", productorder=product.id),
            method="GET",
            title="Get product order for the product",
        )

    def add_control_get_stock(self, product):
        ''' Add control to get stock '''
        self.add_control(
            "product:stock-by-product",
            url_for("api.stockitem", product=product.id),
            method="GET",
            title="Get stock for the product",
        )

    def add_control_get_product(self, product):
        ''' Add control to get product '''
        self.add_control(
            "stock:get-product",
            url_for("api.productitem", product=product.stockProduct.name),
            method="GET",
            title="Get product for the stock",
        )

    def add_control_order(self, productorder):
        ''' Add control to get order '''
        self.add_control(
            "productorder:get-order",
            url_for("api.orderitem", order=productorder.order.id),
            method="GET",
            title="Get order for the productorder",
        )

    def add_control_product(self, productorder):
        ''' Add control to get product '''
        self.add_control(
            "productorder:get-product",
            url_for("api.productitem", product=productorder.product.name),
            method="GET",
            title="Get product for the productorder",
        )

    def add_control_add_product(self):
        ''' Add control to add product '''
        self.add_control_post(
            "product:add-product",
            "Add a new product",
            url_for("api.productcollection"),
            Product.json_schema()
        )

    def add_control_add_customer(self):
        ''' Add control to add customer '''
        self.add_control_post(
            "customer:add-customer",
            "Add a new customer",
            url_for("api.customercollection"),
            Customer.json_schema()
        )

    def add_control_add_order(self):
        ''' Add control to add order '''
        self.add_control_post(
            "order:add-order",
            "Add a new order",
            url_for("api.ordercollection"),
            Order.json_schema()
        )

    def add_control_add_productorder(self):
        ''' Add control to add product order '''
        self.add_control_post(
            "productorder:add-productorder",
            "Add a new product order",
            url_for("api.productordercollection"),
            ProductOrder.json_schema()
        )

    def add_control_edit_customer(self, customer):
        ''' Add control to edit customer '''
        self.add_control_put(
            "Edit a customer",
            url_for("api.customeritem", customer=customer.uuid),
            Customer.json_schema()
        )

    def add_control_edit_product(self, product):
        ''' Add control to edit product '''
        self.add_control_put(
            "Edit a product",
            url_for("api.productitem", product=product.name),
            Product.json_schema()
        )

    def add_control_edit_order(self, order):
        ''' Add control to edit order '''
        self.add_control_put(
            "Edit an order",
            url_for("api.orderitem", order=order.id),
            Order.json_schema()
        )

    def add_control_edit_productorder(self, productorder):
        ''' Add control to edit product order '''
        self.add_control_put(
            "Edit a product order",
            url_for("api.productorderitem", productorder=productorder.id),
            ProductOrder.json_schema()
        )

    def add_control_edit_stock(self, product):
        ''' Add control to edit stock '''
        self.add_control_put(
            "Edit stock",
            url_for("api.stockitem", product=product.productId),
            Stock.json_schema()
        )

    def add_control_delete_product(self, product):
        ''' Add control to delete product '''
        href = url_for("api.productitem", product=product.name)
        self.add_control_delete("Delete a product", href=href)

    def add_control_delete_customer(self, customer):
        ''' Add control to delete customer '''
        href = url_for("api.customeritem", customer=customer.uuid)
        self.add_control_delete("Delete a customer", href=href)

    def add_control_delete_order(self, order):
        ''' Add control to delete order '''
        href = url_for("api.orderitem", order=order.id)
        self.add_control_delete("Delete an order", href=href)

    def add_control_delete_productorder(self, productorder):
        ''' Add control to delete product order '''
        href = url_for("api.productorderitem", productorder=productorder.id)
        self.add_control_delete("Delete a product order", href=href)

    def add_control_delete_stock(self, product):
        ''' Add control to delete stock '''
        href = url_for("api.stockitem", product=product.productId)
        self.add_control_delete("Delete product stock", href=href)


def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)


class ProductConverter(BaseConverter):
    """
    A URL converter for Product objects. It converts between the Product object
    and the string representation of the product's name. The conversion is
    based on the product's name.
    """

    def to_python(self, product_name):  # used in routing
        ''' Convert product name to Product object '''
        db_product = Product.query.filter_by(name=product_name).first()
        if db_product is None:
            raise NotFound
        return db_product

    def to_url(self, db_product):  # used in reverse routing
        ''' Convert Product object to product name '''
        # db_product.name
        # AttributeError: 'str' object has no attribute 'name'
        return str(db_product)


class CustomerConverter(BaseConverter):
    """
    A URL converter for Customer objects. It converts between the Customer
    object and the string representation of the customer's UUID. The conversion
    is based on the customer's UUID.
    """

    def to_python(self, customer_uuid):  # used in routing
        ''' Convert customer UUID to Customer object '''
        db_customer = Customer.query.filter_by(uuid=customer_uuid).first()
        if db_customer is None:
            raise NotFound
        return db_customer

    def to_url(self, db_customer):  # used in reverse routing
        ''' Convert Customer object to customer UUID '''
        return str(db_customer)


class OrderConverter(BaseConverter):
    """
    A URL converter for Order objects. It converts between the Order object
    and the string representation of the order's ID. The conversion is based on
    the order's ID.
    """

    def to_python(self, order_id):  # used in routing
        ''' Convert order ID to Order object '''
        db_order = Order.query.filter_by(id=order_id).first()
        if db_order is None:
            raise NotFound
        return db_order

    def to_url(self, db_order):  # used in reverse routing
        ''' Convert Order object to order ID '''
        return str(db_order)


class ProductOrderConverter(BaseConverter):
    """
    A URL converter for ProductOrder objects. It converts between the ProductOrder
    object and the string representation of the product order's ID. The conversion
    is based on the product order's ID.
    """

    def to_python(self, productOrder_id):  # used in routing
        ''' Convert product order ID to ProductOrder object '''
        db_product_order = ProductOrder.query.filter_by(
            id=productOrder_id).first()
        if db_product_order is None:
            raise NotFound
        return db_product_order

    def to_url(self, db_product_order):  # used in reverse routing
        ''' Convert ProductOrder object to product order ID '''
        return str(db_product_order)


class StockConverter(BaseConverter):
    """
    A URL converter for Stock objects. It converts between the Stock object
    and the string representation of the stock's product ID. The conversion is
    based on the stock's product ID.
    """

    def to_python(self, productId):  # used in routing
        ''' Convert product ID to Stock object '''
        db_stock = Stock.query.filter_by(productId=productId).first()
        if db_stock is None:
            raise NotFound
        return db_stock

    def to_url(self, db_stock):  # used in reverse routing
        ''' Convert Stock object to product ID '''
        return str(db_stock)
