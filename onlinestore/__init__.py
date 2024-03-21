import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

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

    from .utils import ProductConverter, CustomerConverter, OrderConverter, ProductOrderConverter, StockConverter
    app.url_map.converters['product'] = ProductConverter
    app.url_map.converters['customer'] = CustomerConverter
    app.url_map.converters['order'] = OrderConverter
    app.url_map.converters['productorder'] = ProductOrderConverter
    app.url_map.converters['stock'] = StockConverter

    from . import api, models
    app.cli.add_command(models.init_db_command)
    app.register_blueprint(api.api_bp, url_prefix='/api')

    return app


def main():
    app = create_app()
    app.run(debug=True)


if __name__ == '__main__':
    main()
