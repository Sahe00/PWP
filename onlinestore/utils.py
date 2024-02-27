from werkzeug.routing import BaseConverter
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from onlinestore.models import Product


class ProductConverter(BaseConverter):
    def to_python(self, handle_name):  # used in routing
        db_product = Product.query.filter_by(handle=handle_name).first()
        if db_product is None:
            raise NotFound
        return db_product

    def to_url(self, db_product):  # used in reverse routing
        return db_product.handle
