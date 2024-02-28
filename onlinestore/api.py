from flask import Blueprint
from flask_restful import Api, url_for

# import collections
from onlinestore.resources.product import ProductCollection, ProductItem
from onlinestore.resources.customer import CustomerCollection, CustomerItem

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

# Add resources
api.add_resource(ProductCollection, '/products/', methods=['GET', 'POST'])
api.add_resource(ProductItem, '/products/<product:name>', methods=['GET', 'PUT', 'DELETE'])

api.add_resource(CustomerCollection, '/customers/', methods=['GET', 'POST'])
api.add_resource(CustomerItem, '/customers/<customer:uuid>', methods=['GET', 'PUT', 'DELETE'])