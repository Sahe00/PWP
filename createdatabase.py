from app import app
from app import db

# This script creates the database and tables. It should be run once before running the app.

ctx = app.app_context()
ctx.push()
db.create_all()
ctx.pop()
