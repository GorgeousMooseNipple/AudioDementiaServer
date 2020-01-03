import os
import shutil
import re
from mutagen.mp3 import EasyMP3
from ad_server.config import Config
from ad_server.models import (
    Song,
    Artist,
    Album,
    Genre
)
from lastfm_api import search_on_lastfm
from datetime import datetime
from ad_server import create_app, db

app = create_app(Config)
app.app_context().push()
db.init_app(app)

SONGS_FOLDER = Config.DATA_LOCATION
UNPROCESSED_FOLDER = os.path.join(
    SONGS_FOLDER, f'{datetime.now().strftime("%Y-%m-%d")}unprocessed')
ADDED_FOLDER = os.path.join(SONGS_FOLDER, 'added')

reg = re.compile(r'\s*([\s\w\d\-&\.\']*[\w\d])\s*[/,;\\]?')

for f in os.listdir(SONGS_FOLDER):

    if not os.path.isfile(os.path.join(SONGS_FOLDER, f)):
        continue
    elif os.path.splitext(f)[1] != '.mp3':
        continue

    filepath = os.path.abspath(os.path.join(SONGS_FOLDER, f))

    songfile = EasyMP3(filepath)

    title = songfile.tags.get('title') and \
        songfile.tags.get('title')[0]
    track_number = songfile.tags.get('tracknumber') and \
        int(songfile.tags.get('tracknumber')[0].split('/')[0])
    duration = songfile.info.length
    genres_titles = songfile.tags.get('genre') and \
        reg.findall(songfile.tags.get('genre')[0])
    artists_titles = songfile.tags.get('artist') and \
        reg.findall(songfile.tags.get('artist')[0])

    if not title or not artists_titles or len(artists_titles) == 0:
        if not os.path.exists(UNPROCESSED_FOLDER):
            os.mkdir(UNPROCESSED_FOLDER)
        shutil.move(filepath, os.path.join(UNPROCESSED_FOLDER, f))
        continue

    artists = []

    for artist_title in artists_titles:
        artist = Artist.query.filter_by(title=artist_title).first()
        if not artist:
            artist = Artist(title=artist_title)
            db.session.add(artist)
        artists.append(artist)

    album_title = songfile.tags.get('album') and songfile.tags.get('album')[0]

    try:
        if not album_title:
            track_info = search_on_lastfm(
                searchfor='track', track=title, artist=artists_titles[0]
                )
            album_title = track_info['album']['title']

        album = Album.query.filter_by(title=album_title) \
                     .join(Album.artists).filter_by(title=artist_title).first()
        if not album:
            album_info = search_on_lastfm(
                searchfor='album', album=album_title, artist=artists_titles[0]
                )
            cover_small = album_info.get('image')[1].get('#text')
            cover_medium = album_info.get('image')[2].get('#text')
            album = Album(
                title=album_title,
                cover_small=cover_small,
                cover_medium=cover_medium)
            album.artists.extend(
                [a for a in artists if a not in album.artists]
                )
            db.session.add(album)

    except ConnectionError as e:
        print(repr(e))

    if album and genres_titles:
        genres = []
        for genre_title in genres_titles:
            genre = Genre.query.filter_by(title=genre_title).first()
            if not genre:
                genre = Genre(title=genre_title)
                db.session.add(genre)
            genres.append(genre)
        album.genres.extend([g for g in genres if g not in album.genres])

    if len(artists) == 1:
        single_artist = artists[0]

    song = Song(
        title=title,
        filepath=filepath,
        duration=duration,
        album_position=track_number,
        artist=single_artist,
        album=album)
    db.session.add(song)
    db.session.commit()

    if not os.path.exists(ADDED_FOLDER):
        os.mkdir(ADDED_FOLDER)
    shutil.move(filepath, os.path.join(ADDED_FOLDER, f))
