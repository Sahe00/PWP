import json
import uuid
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    uuid = db.Column(db.String(36), default=str(uuid.uuid4()), unique=True, nullable=False)
    firstName = db.Column(db.String(50), nullable=False)
    lastName = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=True)
    phone = db.Column(db.String(50), nullable=True)

    orders = db.relationship('Order', back_populates="customer")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)

    # Set foreign key to null if customer is deleted
    customerId = db.Column(db.Integer, db.ForeignKey('customer.id', ondelete="SET NULL"))

    createdAt = db.Column(db.String(50), nullable=False)

    customer = db.relationship('Customer', back_populates="orders")
    productOrder = db.relationship('ProductOrder', cascade="all, delete-orphan", back_populates="order")

class ProductOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    orderId = db.Column(db.Integer, db.ForeignKey('order.id', ondelete="CASCADE"), nullable=False)
    productId = db.Column(db.Integer, db.ForeignKey('product.id', ondelete="SET NULL"))
    quantity = db.Column(db.Integer, nullable=False)

    order = db.relationship('Order', back_populates="productOrder")
    product = db.relationship('Product', back_populates="products")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    desc = db.Column(db.String(128), nullable=False)
    price = db.Column(db.Float, nullable=False)

    products = db.relationship('ProductOrder', back_populates="product")
    stock = db.relationship('Stock', cascade="all, delete-orphan", back_populates="stockProduct")

class Stock(db.Model):
    productId = db.Column(db.Integer, db.ForeignKey('product.id', ondelete="CASCADE"), primary_key=True, nullable=False)
    quantity = db.Column(db.Integer)

    stockProduct = db.relationship('Product', back_populates="stock")
