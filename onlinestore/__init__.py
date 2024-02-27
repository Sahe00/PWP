import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    from . import api, models
    app.cli.add_command(models.init_db_command)
    app.register_blueprint(api.api_bp, url_prefix='/api')


    return app


def main():
    app = create_app()
    app.run(debug=True)


if __name__ == '__main__':
    main()
