import tests.conftest
from ad_server.utils.addsongs import add_songs_to_db
from ad_server.models import Song, Album, Genre
import os


test_app = tests.conftest.test_app
audio_files_fixture = tests.conftest.audio_files_fixture


def test_script_adding_songs_to_db(test_app, audio_files_fixture):
    media_folder = audio_files_fixture
    db = test_app['db']
    add_songs_to_db(media_folder, db)

    # Script should've added two songs from test folder to db
    assert Song.query.count() == 2
    # One new album
    assert Album.query.count() == 1
    # Two new genres
    assert Genre.query.count() == 2

    album = Album.query.first()

    # Album cover from last fm api call should've been added to db
    assert album.cover_small and album.cover_medium

    songs = Song.query.all()

    for song in songs:
        # Songs must've been placed in added directory within
        # servers media storage
        # this path then written in database
        assert os.path.dirname(song.filepath) == \
            os.path.join(media_folder, 'added')
