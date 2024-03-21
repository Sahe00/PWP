from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from onlinestore.models import Product, Customer, Order, ProductOrder, Stock


class ProductConverter(BaseConverter):
    def to_python(self, name):  # used in routing
        db_product = Product.query.filter_by(name=name).first()
        if db_product is None:
            raise NotFound
        return db_product

    def to_url(self, db_product):  # used in reverse routing
        return db_product.name


class CustomerConverter(BaseConverter):
    def to_python(self, uuid):  # used in routing
        db_customer = Customer.query.filter_by(uuid=uuid).first()
        if db_customer is None:
            raise NotFound
        return db_customer

    def to_url(self, db_customer):  # used in reverse routing
        return db_customer.uuid


class OrderConverter(BaseConverter):
    def to_python(self, id):  # used in routing
        db_order = Order.query.filter_by(id=id).first()
        if db_order is None:
            raise NotFound
        return db_order

    def to_url(self, db_order):  # used in reverse routing
        return db_order.id


class ProductOrderConverter(BaseConverter):
    def to_python(self, id):  # used in routing
        db_product_order = ProductOrder.query.filter_by(id=id).first()
        if db_product_order is None:
            raise NotFound
        return db_product_order

    def to_url(self, db_product_order):  # used in reverse routing
        return db_product_order.id


class StockConverter(BaseConverter):
    def to_python(self, productId):  # used in routing
        db_stock = Stock.query.filter_by(productId=productId).first()
        if db_stock is None:
            raise NotFound
        return db_stock

    def to_url(self, db_stock):  # used in reverse routing
        return db_stock.productId
