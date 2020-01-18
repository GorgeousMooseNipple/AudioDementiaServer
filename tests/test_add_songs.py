from ad_server.utils.addsongs import add_songs_to_db
from ad_server.models import Song, Album, Genre, AlbumGenre, AlbumArtist
import os


def test_script_adding_songs_to_db(app, app_db, audio_storage):

    add_songs_to_db(audio_storage, app_db)

    assert Song.query.count() != 0
    assert Album.query.count() != 0
    assert Genre.query.count() != 0
    assert AlbumArtist.query.count() != 0
    assert AlbumGenre.query.count() != 0

    album = Album.query.first()

    # Album cover from last fm api call should've been added to db
    assert album.cover_small and album.cover_medium

    songs = Song.query.all()

    for song in songs:
        # Songs must've been placed in added directory within
        # servers media storage
        # this path then written in database
        assert os.path.dirname(song.filepath) == \
            os.path.join(audio_storage, 'added')
