from ad_server import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# from sqlalchemy import MetaData
# meta = MetaData(db.engine)
# meta.reflect()
# __table__ = meta.tables['tablename']


class BaseModel:
    def to_dict(self):
        d = {}
        for attr in self.__class__.__dict__.keys():
            if attr.startswith('_'):
                continue
            val = getattr(self, attr)
            if callable(val):
                continue
            d[attr] = val
        return d


class User(db.Model, BaseModel, UserMixin):
    __tablename__ = 'app_user'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    login = db.Column('login', db.String(64), nullable=False, unique=True)
    pass_hash = db.Column('pass_hash', db.String(128), nullable=False)
    playlists = db.relationship('Playlist', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.pass_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pass_hash, password)


class Song(db.Model, BaseModel):
    __tablename__ = 'song'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    filepath = db.Column('filepath', db.String(128), nullable=False)
    duration = db.Column('duration', db.Integer)
    album_position = db.Column('album_position', db.SmallInteger)
    listens_count = db.Column('listens_count', db.Integer, default=0)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'))


class Artist(db.Model, BaseModel):
    __tablename__ = 'artist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False, unique=True)
    songs = db.relationship('Song', backref='artist', lazy='dynamic')
    albums = db.relationship('Album', secondary='album_artist', back_populates='artists')


class Album(db.Model, BaseModel):
    __tablename__ = 'album'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False, default='unknown')
    year = db.Column('year', db.SmallInteger)
    cover_small = db.Column('cover_small', db.String(256))
    cover_medium = db.Column('cover_medium', db.String(256))
    songs = db.relationship('Song', backref='album', lazy='dynamic')
    genres = db.relationship('Genre', secondary='album_genre', back_populates='albums')
    artists = db.relationship('Artist', secondary='album_artist', back_populates='albums')


class Genre(db.Model, BaseModel):
    __tablename__ = 'genre'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False, unique=True)
    title = db.Column('title', db.String(64), nullable=False, unique=True)
    albums = db.relationship('Album', secondary='album_genre', back_populates='genres')


class AlbumGenre(db.Model, BaseModel):
    __tablename__ = 'album_genre'
    id = db.Column('id', db.Integer, primary_key=True)
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'), nullable=False)
    genre_id = db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)


class Playlist(db.Model, BaseModel):
    __tablename__ = 'playlist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    song_count = db.Column('song_count', db.Integer)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('app_user.id'))


class AlbumArtist(db.Model, BaseModel):
    __tablename__ = 'album_artist'
    id = db.Column('id', db.Integer, primary_key=True)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('artist_id', 'album_id'),)


class PlaylistSong(db.Model, BaseModel):
    __tablename__ = 'playlist_song'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    playlist_id = db.Column(
                        'playlist_id',
                        db.Integer,
                        db.ForeignKey('playlist.id'))
    song_id = db.Column('song_id', db.Integer, db.ForeignKey('song.id'))
    song_position = db.Column('song_position', db.Integer)