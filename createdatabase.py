from datetime import datetime
from app import app
from app import db
from app import Customer, Order, Product, Stock, ProductOrder

# This script creates the database and tables. It should be run once before running the app.

ctx = app.app_context()
ctx.push()
db.create_all()
# ctx.pop()

antti = Customer(
    firstName="Antti",
    lastName="Heikkinen",
    email="a.heikkinen@luukku.com",
    phone="04012345667"
)

satikka = Product(
    name="Sateenvarjo",
    desc="Sateenvarjo suojaa sinua sateelta kuin sateelta!",
    price=20.00
)

kumpparit = Product(
    name="Kumpparit",
    desc="Kumiset saappaat, pitävät varpaasi kuivana!",
    price=10.00
)

antin_tilaus = Order(
    customer=antti,
    createdAt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
)

antin_tuote_1 = ProductOrder(
    order=antin_tilaus,
    product=satikka,
    quantity=2
)

antin_tuote_2 = ProductOrder(
    order=antin_tilaus,
    product=kumpparit,
    quantity=1
)

satikkavarasto = Stock(
    quantity=8,
    stockProduct=satikka
)

kumpparivarasto = Stock(
    quantity=20,
    stockProduct=kumpparit
)

db.session.add_all(
    [
        antti,
        satikka,
        kumpparit,
        antin_tilaus,
        antin_tuote_1,
        antin_tuote_2,
        satikkavarasto,
        kumpparivarasto
    ]
)
db.session.commit()
ctx.pop()
