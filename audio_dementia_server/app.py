from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from audio_dementia_server.appconfig import CONFIG

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = CONFIG['connection']
db = SQLAlchemy(app)


if __name__ == '__main__':
    app.run()