from flask import Flask
from ad_server.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


db = SQLAlchemy()
migrate = Migrate()


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)
    migrate.init_app(app, db)

    from ad_server.views.users import users as users_bp
    app.register_blueprint(users_bp, url_prefix='/api/public/auth')

    return app


from ad_server import models
