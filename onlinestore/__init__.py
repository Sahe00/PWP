'''
API Initialization
'''
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
from onlinestore.constants import *


db = SQLAlchemy()


def create_app(test_config=None):
    ''' Create and configure the app '''
    app = Flask(__name__, instance_relative_config=True)

    app.config["SWAGGER"] = {
        "title": "Online Store API",
        "openapi": "3.0.3",
        "uiversion": 3
    }
    # swagger = Swagger(app)

    default_config = {
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        "SQLALCHEMY_DATABASE_URI": 'sqlite:///test.db'
    }

    if test_config is None:
        # For production purposes
        app.config.from_mapping(default_config)
    else:
        # For testing purposes
        app.config.from_mapping(test_config)

    db.init_app(app)

    from onlinestore import api, models
    from onlinestore.utils import ProductConverter, CustomerConverter, OrderConverter
    from onlinestore.utils import ProductOrderConverter, StockConverter
    app.url_map.converters["product"] = ProductConverter
    app.url_map.converters["customer"] = CustomerConverter
    app.url_map.converters["order"] = OrderConverter
    app.url_map.converters["productorder"] = ProductOrderConverter
    app.url_map.converters["stock"] = StockConverter

    app.cli.add_command(models.init_db_command)
    app.register_blueprint(api.api_bp, url_prefix='/api')

    @app.route(LINK_RELATIONS_URL)
    def send_link_relations():
        return "link relations"

    @app.route("/profiles/<profile>/")
    def send_profile(profile):
        return f"you requests {profile} profile"

    return app


def main():
    ''' Run the app '''
    app = create_app()
    app.run(debug=True)


if __name__ == '__main__':
    main()
