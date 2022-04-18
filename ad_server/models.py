import os
import base64

from ad_server import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_sqlalchemy import BaseQuery
from sqlalchemy.exc import SQLAlchemyError
from ad_server.views.error import RefreshTokenError


# from sqlalchemy import MetaData
# meta = MetaData(db.engine)
# meta.reflect()
# __table__ = meta.tables['tablename']


# Key based pagination
def paginate(query, per_page, key, last=0):
    return query.filter(key > last).order_by(key).limit(per_page)


class BaseModel:
    def to_dict(self):
        """
        Returns model attributes as a dict.
        Format is <attribute_name>: <value>.
        May be useful for convertion to json.
        """
        d = {}
        for attr in self.__class__.__dict__.keys():
            if attr.startswith('_'):
                continue
            val = getattr(self, attr)

            # Only model attributes, no methods.
            # Also excludes dynamic relationships and models.
            if callable(val) or \
               isinstance(val, BaseQuery) or \
               isinstance(val, db.Model):
                continue

            d[attr] = val
        return d


class User(db.Model, BaseModel):
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

    def get_playlists(self):
        playlists = [p.to_dict() for p in self.playlists]
        return playlists


class Song(db.Model, BaseModel):
    __tablename__ = 'song'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    filepath = db.Column('filepath', db.String(128), nullable=False)
    duration = db.Column('duration', db.Integer)
    album_position = db.Column('album_position', db.SmallInteger)
    listens_count = db.Column('listens_count', db.Integer, default=0)
    artist_id = db.Column(
        'artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'))

    @staticmethod
    def play_song(id):
        song = Song.query.get(id)
        if song:
            song.listens_count += 1
            db.session.add(song)
            return song.filepath
        else:
            return None

    def to_dict(self):
        d = {
            'id': self.id,
            'title': self.title,
            'album_position': self.album_position,
            'duration': self.duration,
        }

        cover_small = None
        cover_medium = None
        artists = []
        if self.album:
            artists.extend([a.title for a in self.album.artists])
            cover_small = self.album.cover_small
            cover_medium = self.album.cover_medium
        else:
            artists.append(self.artist.title)
        album_title = self.album.title if self.album else 'unknown'

        d['artists'] = artists
        d['album'] = album_title
        d['cover_small'] = cover_small
        d['cover_medium'] = cover_medium

        return d

    @staticmethod
    def get_by_title(title, per_page=20, last=0):
        search = f'%{title}%'

        try:
            query = Song.query.filter(Song.title.ilike(search))
            songs = paginate(query, per_page, key=Song.id, last=last)
        except SQLAlchemyError:
            return None

        return [s.to_dict() for s in songs]

    @staticmethod
    def get_by_artist_title(title, per_page=20, last=0):
        search = f'%{title}%'

        try:
            query = Song.query.outerjoin(Album).outerjoin(AlbumArtist)\
                .join(
                    Artist,
                    (Artist.id == Song.artist_id) |
                    (Artist.id == AlbumArtist.artist_id)
                    ).filter(Artist.title.ilike(search))
            songs = paginate(query, per_page, key=Song.id, last=last)
        except SQLAlchemyError:
            return None

        return [s.to_dict() for s in songs]


class Artist(db.Model, BaseModel):
    __tablename__ = 'artist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False, unique=True)
    songs = db.relationship('Song', backref='artist', lazy='dynamic')
    albums = db.relationship(
        'Album',
        secondary='album_artist',
        back_populates='artists',
        lazy='dynamic')


class Album(db.Model, BaseModel):
    __tablename__ = 'album'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column(
        'title', db.String(64), nullable=False, default='unknown')
    year = db.Column('year', db.SmallInteger)
    cover_small = db.Column('cover_small', db.String(256))
    cover_medium = db.Column('cover_medium', db.String(256))
    songs = db.relationship(
        'Song',
        backref='album',
        lazy='dynamic',
        order_by='Song.album_position')
    genres = db.relationship(
        'Genre',
        secondary='album_genre',
        back_populates='albums',
        lazy='dynamic')
    artists = db.relationship(
        'Artist',
        secondary='album_artist',
        back_populates='albums',
        lazy='dynamic')

    def to_dict(self):
        d = super().to_dict()
        d['genres'] = [g.title for g in self.genres]
        artists = []
        for artist in self.artists:
            artists.append(artist.title)
        d['artists'] = artists
        return d

    @staticmethod
    def get_top(limit=5):
        # Aggregate function. Sum of listens for songs
        p = db.func.sum(Song.listens_count)

        sess = db.session
        # Selects album sorted
        try:
            top_albums = sess.query(Album).join(Album.songs)\
                .group_by(Album).order_by(-p).limit(limit)
        except SQLAlchemyError:
            sess.rollback()
            return None

        return [a.to_dict() for a in top_albums]

    def get_songs(self):
        """
        Returns list of songs from album in dict representation.
        This list is sorted by song position in the album
        thanks to order_by argument in relationship
        """
        songs = [s.to_dict() for s in self.songs]
        return songs

    @staticmethod
    def get_by_title(title, per_page=20, last=0):
        search = f'%{title}%'

        try:
            query = Album.query.filter(Album.title.ilike(search))
            albums = paginate(
                query, per_page=per_page, key=Album.id, last=last)
        except SQLAlchemyError:
            return None

        return [a.to_dict() for a in albums]


class Genre(db.Model, BaseModel):
    __tablename__ = 'genre'
    id = db.Column(
        'id', db.Integer, primary_key=True, nullable=False, unique=True)
    title = db.Column('title', db.String(64), nullable=False, unique=True)
    albums = db.relationship(
        'Album',
        secondary='album_genre',
        back_populates='genres',
        lazy='dynamic')

    @staticmethod
    def get_top(limit=5):
        # Aggregate function. Sum of listens for songs
        p = db.func.sum(Song.listens_count)

        sess = db.session
        # Selects genres sorted
        try:
            top_genres = sess.query(Genre).join(AlbumGenre).join(Album.songs)\
                .group_by(Genre).order_by(-p).limit(limit).all()
        except SQLAlchemyError:
            sess.rollback()
            return None

        return [g.to_dict() for g in top_genres]

    def get_songs(self, per_page=20, last=0):
        sess = db.session

        try:
            query = sess.query(Song).join(Album).join(AlbumGenre)\
                .filter(AlbumGenre.genre_id == self.id)
            songs = paginate(query, per_page, key=Song.id, last=last)
        except SQLAlchemyError:
            sess.rollback()
            return None

        return [s.to_dict() for s in songs]


class AlbumGenre(db.Model, BaseModel):
    __tablename__ = 'album_genre'
    id = db.Column('id', db.Integer, primary_key=True)
    album_id = db.Column(
        'album_id', db.Integer, db.ForeignKey('album.id'), nullable=False)
    genre_id = db.Column(
        'genre_id', db.Integer, db.ForeignKey('genre.id'), nullable=False)


class Playlist(db.Model, BaseModel):
    __tablename__ = 'playlist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('app_user.id'))
    songs = db.relationship(
        'Song',
        secondary='playlist_song',
        lazy='dynamic'
        )

    def to_dict(self):
        song_count = Playlist.query.get(self.id).songs.count()
        d = {
            'id': self.id,
            'title': self.title,
            'song_count': song_count,
        }
        return d

    def get_songs(self, per_page=20, last=0):
        """
        Returns list of songs from playlist in dict representation.
        This list is sorted by song position in playlist
        """
        try:
            songs = paginate(
                self.songs,
                per_page,
                key=PlaylistSong.song_position,
                last=last
                )
        except SQLAlchemyError:
            return None
        return [s.to_dict() for s in songs]

    def add_song(self, song):
        """
        Adds song to playlist
        """
        # Calculate song position in this playlist
        song_position = PlaylistSong.query\
            .filter_by(playlist_id=self.id).count() + 1

        # Create new row in secondary relational table
        ps = PlaylistSong(
            playlist_id=self.id,
            song_id=song.id,
            song_position=song_position
        )

        db.session.add(ps)


class AlbumArtist(db.Model, BaseModel):
    __tablename__ = 'album_artist'
    id = db.Column('id', db.Integer, primary_key=True)
    artist_id = db.Column(
        'artist_id', db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column(
        'album_id', db.Integer, db.ForeignKey('album.id'), nullable=False)
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


class RefreshToken(db.Model):
    __tablename__ = 'refresh_token'
    token = db.Column('token', db.String(32), primary_key=True)
    expiration_date = db.Column(
        'expiration_date', db.DateTime, default=datetime.utcnow)
    user_id = db.Column(
        'user_id', db.Integer, db.ForeignKey('app_user.id'),
        nullable=False, unique=True)

    @staticmethod
    def create_or_get(user_id, expires_in=timedelta(weeks=24)):
        # If already exists for this user
        refresh_token = RefreshToken.query.join(User).filter_by(id=user_id).first()
        if refresh_token:
            return refresh_token.token
            # raise RefreshTokenError('Refresh token is already given to this user')
        return RefreshToken.create(user_id, expires_in) 


    @staticmethod
    def create(user_id, expires_in=timedelta(weeks=24)):
        if isinstance(expires_in, int):
            delta = timedelta(weeks=expires_in)
        elif isinstance(expires_in, timedelta):
            delta = expires_in
        else:
            raise RefreshTokenError(
                'expires_in value must be either integer in weeks or'
                'datetime.timedelta'
            )
        token = base64.b64encode(os.urandom(24)).decode('utf-8')
        expiration_date = datetime.utcnow() + delta
        refresh_token = RefreshToken(
            token=token,
            user_id=user_id,
            expiration_date=expiration_date)
        db.session.add(refresh_token)
        return token

    @staticmethod
    def valid_token(token):
        refresh_token = RefreshToken.query.get(token)
        if refresh_token and datetime.utcnow() < refresh_token.expiration_date:
            return refresh_token
        return None

    @staticmethod
    def revoke(token):
        RefreshToken.query.filter_by(token=token).delete()

    @staticmethod
    def get_user(token):
        User.query.join(RefreshToken).filter_by(token=token).first()
