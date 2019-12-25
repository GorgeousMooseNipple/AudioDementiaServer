from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from ad_server.appconfig import CONFIG
from ad_server.routes import api

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = CONFIG['connection']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.register_blueprint(api, url_prefix='/api/public')

if __name__ == '__main__':
    app.run()
