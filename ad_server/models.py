from ad_server.app import db


# from sqlalchemy import MetaData
# meta = MetaData(db.engine)
# meta.reflect()
# __table__ = meta.tables['tablename']


class User(db.Model):
    __tablename__ = 'app_user'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    login = db.Column('login', db.String(64), nullable=False, unique=True)
    pass_hash = db.Column('pass_hash', db.String(64), nullable=False)


class Song(db.Model):
    __tablename__ = 'song'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    file_path = db.Column('file_path', db.String(128), nullable=False)
    duration = db.Column('duration', db.BigInteger())
    album_position = db.Column('album_position', db.SmallInteger())
    cover_small = db.Column('cover_small', db.String(256))
    cover_medium = db.Column('cover_medium', db.String(256))
    listens_count = db.Column('listens_count', db.BigInteger())
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'))
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'))
    genre_id = db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'))


class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False, unique=True)


class Album(db.Model):
    __tablename__ = 'album'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    year = db.Column('year', db.SmallInteger())
    cover_small = db.Column('cover_small', db.String(256))
    cover_medium = db.Column('cover_medium', db.String(256))


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)


class Playlist(db.Model):
    __tablename__ = 'playlist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    title = db.Column('title', db.String(64), nullable=False)
    song_count = db.Column('song_count', db.BigInteger())
    user_id = db.Column('user_id', db.Integer, db.ForeignKey('app_user.id'))


class AlbumArtist(db.Model):
    __tablename__ = 'album_artist'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'))
    album_id = db.Column('album_id', db.Integer, db.ForeignKey('album.id'))
    __table_args__ = (db.UniqueConstraint('artist_id', 'album_id'),)


class PlaylistSong(db.Model):
    __tablename__ = 'playlist_song'
    id = db.Column('id', db.Integer, primary_key=True, nullable=False)
    playlist_id = db.Column(
                        'playlist_id',
                        db.Integer(),
                        db.ForeignKey('playlist.id'))
    song_id = db.Column('song_id', db.Integer(), db.ForeignKey('song.id'))
    song_position = db.Column('song_position', db.BigInteger())
