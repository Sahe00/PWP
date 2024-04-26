'''
API Blueprint and API resources
'''
from flask import Blueprint
from flask_restful import Api

# import collections
from onlinestore.resources.customer import CustomerCollection, CustomerItem
from onlinestore.resources.order import OrderCollection, OrderItem
from onlinestore.resources.product import ProductCollection, ProductItem
from onlinestore.resources.productorder import ProductOrderCollection, ProductOrderItem
from onlinestore.resources.stock import StockCollection, StockItem

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

# Add resources
api.add_resource(ProductCollection, '/products/', methods=['GET', 'POST'])
api.add_resource(ProductItem, '/products/<product:product>/', methods=['GET', 'PUT', 'DELETE'])

api.add_resource(CustomerCollection, '/customers/', methods=['GET', 'POST'])
api.add_resource(CustomerItem, '/customers/<customer:customer>/', methods=['GET', 'PUT', 'DELETE'])

api.add_resource(OrderCollection, '/orders/', methods=['GET', 'POST'])
api.add_resource(OrderItem, '/orders/<order:order>/', methods=['GET', 'PUT', 'DELETE'])

api.add_resource(ProductOrderCollection, '/productorders/', methods=['GET', 'POST'])
api.add_resource(ProductOrderItem, '/productorders/<productorder:productorder>/',
                 methods=['GET', 'PUT', 'DELETE'])

api.add_resource(StockCollection, '/stock/', methods=['GET'])
api.add_resource(StockItem, '/stock/<stock:product>/', methods=['GET', 'PUT', 'DELETE'])
