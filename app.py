import json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    phone = db.Column(db.String(50))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customerId = db.Column(db.Integer, db.ForeignKey('customer.id'))
    customer = db.relationship('Customer', backref=db.backref('orders', lazy=True))

class ProductOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orderId = db.Column(db.Integer, db.ForeignKey('order.id'))
    productId = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    desc = db.Column(db.String(128))
    price = db.Column(db.Float)

class Stock(db.Model):
    productId = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
