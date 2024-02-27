from flask import Blueprint
from flask_restful import Api, url_for

# import collections
from onlinestore.resources.product import ProductCollection, ProductItem

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

# Add resources
api.add_resource(ProductCollection, '/products/', methods=['GET', 'POST'])
api.add_resource(ProductItem, '/products/<name>')
