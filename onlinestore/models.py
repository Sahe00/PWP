import uuid
import click
from flask.cli import with_appcontext
from onlinestore import db


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=True)

    orders = db.relationship('Order', back_populates="customer")

    def serialize(self):
        return {
            'uuid': self.uuid,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'email': self.email,
            'phone': self.phone
        }

    def deserialize(self, data):
        self.firstName = data['firstName']
        self.lastName = data['lastName']
        self.email = data['email']
        self.phone = data.get('phone')

    @staticmethod
    def json_schema():
        return {
            "type": "object",
            "properties": {
                "firstName": {"type": "string"},
                "lastName": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"}
            },
            "required": ["firstName", "lastName", "email"]
        }


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)

    # Set foreign key to null if customer is deleted
    customerId = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete="SET NULL"))
    createdAt = db.Column(db.String(50), nullable=False)

    customer = db.relationship('Customer', back_populates="orders")
    productOrders = db.relationship(
        'ProductOrder', cascade="all, delete-orphan", back_populates="order")

    def serialize(self):
        return {
            'id': self.id,
            'customerId': self.customerId,
            'createdAt': self.createdAt
        }

    def deserialize(self, data):
        self.customerId = data['customerId']
        self.createdAt = data['createdAt']

    @staticmethod
    def json_schema():
        return {
            "type": "object",
            "properties": {
                "customerId": {"type": "integer"},
                "createdAt": {"type": "string"}
            },
            "required": ["customerId", "createdAt"]
        }


class ProductOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), nullable=False)
    productId = db.Column(db.Integer, db.ForeignKey('product.id', ondelete="SET NULL"))
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', back_populates="productOrders")
    product = db.relationship('Product', back_populates="productOrder")

    def serialize(self):
        return {
            'id': self.id,
            'orderId': self.orderId,
            'productId': self.productId,
            'quantity': self.quantity
        }

    def deserialize(self, data):
        self.orderId = data['orderId']
        self.productId = data['productId']
        self.quantity = data['quantity']

    @staticmethod
    def json_schema():
        # Quantity must be a positive integer
        return {
            "type": "object",
            "properties": {
                "orderId": {"type": "integer"},
                "productId": {"type": "integer"},
                "quantity": {"type": "integer", "minimum": 0}
            },
            "required": ["orderId", "productId", "quantity"]
        }


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    desc = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)

    productOrder = db.relationship('ProductOrder', back_populates="product")
    stock = db.relationship('Stock', cascade="all, delete-orphan", back_populates="stockProduct")

    def serialize(self):
        return {
            "name": self.name,
            "desc": self.desc,
            "price": self.price
        }

    def deserialize(self, data):
        self.name = data['name']
        self.desc = data['desc']
        self.price = data['price']

    @staticmethod
    def json_schema():
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "desc": {"type": "string"},
                "price": {"type": "number"}
            },
            "required": ["name", "desc", "price"]
        }


class Stock(db.Model):
    productId = db.Column(db.Integer, db.ForeignKey(
        'product.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    quantity = db.Column(db.Integer)

    stockProduct = db.relationship('Product', back_populates="stock")

    def serialize(self):
        return {
            "productId": self.productId,
            "quantity": self.quantity
        }

    def deserialize(self, data):
        self.productId = data.get('productId')
        self.quantity = data.get('quantity')

    @staticmethod
    def json_schema():
        # Quantity must be a positive integer
        return {
            "type": "object",
            "properties": {
                "productId": {"type": "integer"},
                "quantity": {"type": "integer", "minimum": 0}
            },
            "required": ["quantity"]
        }


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
