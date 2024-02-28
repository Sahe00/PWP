from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from onlinestore.models import Product, Customer


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
