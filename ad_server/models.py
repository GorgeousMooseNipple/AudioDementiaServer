from audio_dementia_server.app import db


class User(db.Model):
    __tablename__ = 'app_user'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    login = db.Column('login', db.String(64), nullable=False, unique=True)
    pass_hash = db.Column('pass_hash', db.String(64), nullable=False)
    # __table__ = db.Table(
    #     'app_user',
    #     db.Model.metadata,
    #     autoload=True,
    #     autoload_with=db.engine)
