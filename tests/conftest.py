import pytest
import requests
import os
import shutil
import ad_server.views.messages as msg
from ad_server import create_app, db
from ad_server.config import TestConfig
from ad_server.models import (
    User,
    RefreshToken,
    Playlist,
    Song,
    Album,
    Artist,
    Genre
    )
from ad_server.views.auth import generate_token, token_auth
from flask import current_app, testing


PWD = os.path.dirname(os.path.abspath(__file__))


class TestClient(testing.FlaskClient):
    """
    Custom flask test client with default headers
    """

    default_headers = {}

    def open(self, *args, **kwargs):
        # default_headers = {'Content-Type': 'application/json'}
        headers = kwargs.pop('headers', {})
        headers.update(TestClient.default_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(scope='session', autouse=True)
def app():
    """
    Fixture creates app with test config and pushes context.
    Also some users added to db.
    """
    app = create_app(TestConfig)
    context = app.test_request_context()
    context.push()

    app.test_client_class = TestClient

    db.create_all()

    user = User(login='TestUser', password='testpass')
    logged_user = User(login='LoggedUser', password='testpass')

    db.session.add(user)
    db.session.add(logged_user)
    db.session.commit()

    yield app

    db.drop_all()
    os.remove(os.path.join(PWD, 'test.db'))
    context.pop()


@pytest.fixture(scope='function')
def test_client(app):

    TestClient.default_headers = {}

    with app.test_client() as client:
        return client


@pytest.fixture(scope='function')
def test_client_json(app):

    TestClient.default_headers = {
        'Content-Type': 'application/json'
    }

    with app.test_client() as client:
        return client


@pytest.fixture(scope='session', autouse=True)
def token_endpoint(app):
    """
    Creates fake api endpoint which requires token to access
    """
    @app.route('/test/token/access', methods=['GET'])
    @token_auth.login_required
    def test_token_access():
        return msg.success('Successful API call with token required')


@pytest.fixture(scope='function')
def app_db(app):
    return db


@pytest.fixture(scope='function')
def user_with_tokens():
    """
    Function scope fixture.
    Creates access and refresh tokens for user.
    Returns this user and his tokens.
    On teardown revokes refresh token
    """
    user = User.query.filter_by(login='LoggedUser').first()
    access_token = generate_token(user.id)
    refresh_token = RefreshToken.create(user.id)
    db.session.commit()

    yield user, access_token, refresh_token

    RefreshToken.revoke(refresh_token)
    db.session.commit()


@pytest.fixture(scope='session')
def audio_storage(app):
    """
    This fixture downloads and prepares mp3 files for tests
    to test adding such files into database
    """
    # Create folder for audio files during tests
    media_folder = os.path.join(PWD, 'test_media')
    current_app.config['MEDIA_STORAGE'] = media_folder

    songs_urls = TestConfig.SONGS_URLS

    if not os.path.exists(media_folder):
        os.mkdir(media_folder)

    for i, song_url in enumerate(songs_urls.split('<sep>')):
        r = requests.get(song_url, stream=True)
        if r.status_code == 200:
            song_file = os.path.join(media_folder, f'song{i}.mp3')
            with open(song_file, 'wb+') as f:
                for chunck in r.iter_content(1024):
                    f.write(chunck)

    yield media_folder

    shutil.rmtree(media_folder)


@pytest.fixture(scope='module')
def fill_db(audio_storage):
    """
    Fill database with fake albums, artists, genres and songs for test purposes
    """
    if os.path.exists(os.path.join(audio_storage, 'added')):
        audio_storage = os.path.join(audio_storage, 'added')

    artist1 = Artist(title='artist1')
    db.session.add(artist1)
    artist2 = Artist(title='artist2')
    db.session.add(artist2)

    album1 = Album(title='album1')
    db.session.add(album1)
    album2 = Album(title='album2')
    db.session.add(album2)

    genre1 = Genre(title='genre1')
    db.session.add(genre1)
    genre2 = Genre(title='genre2')
    db.session.add(genre2)

    album1.artists.append(artist1)
    album2.artists.append(artist2)

    album1.genres.append(genre1)
    album2.genres.append(genre2)

    db.session.commit()

    # Filepath for one of loaded mp3 files from audio_storage
    # Will be used as filepath for all test songs in db
    loaded_song = os.path.join(audio_storage, os.listdir(audio_storage)[0])

    artists = [artist1, artist2]
    albums = [album1, album2]

    for i in range(10):
        song = Song(
            title=f'song{i}',
            filepath=loaded_song,
            artist_id=artists[i % len(artists)].id,
            album_id=albums[i % len(artists)].id
            )
        db.session.add(song)

    yield

    Song.query.delete()
    Album.query.delete()
    Artist.query.delete()
    db.session.commit()


@pytest.fixture(scope='function')
def user_with_playlist(fill_db):
    """
    Returns user with created playlist and his tokens.
    Uses data from fill_db fixture.
    """
    user = User(login='PlaylistUser', password='testpass')
    db.session.add(user)
    db.session.commit()

    access_token = generate_token(user.id)
    refresh_token = RefreshToken.create(user.id)

    playlist = Playlist(title='testlist', user_id=user.id)
    db.session.add(playlist)
    db.session.commit()

    songs = Song.query.all()
    for s in songs:
        playlist.add_song(s)
    db.session.commit()

    yield user, access_token, refresh_token

    RefreshToken.revoke(refresh_token)
    db.session.delete(playlist)
    db.session.delete(user)
    db.session.commit()


@pytest.fixture(scope='function')
def songs_for_search(app):
    """
    Creates in db songs with special titles for testing search by title views.
    """
    artist = Artist(title='searchme')
    db.session.add(artist)

    songs = [
        Song(title='search1', artist=artist, filepath=''),
        Song(title='search2', artist=artist, filepath='')
        ]

    for s in songs:
        db.session.add(s)

    db.session.commit()

    yield songs, artist

    for s in songs:
        db.session.delete(s)
    db.session.delete(artist)
    db.session.commit()


@pytest.fixture(scope='function')
def albums_for_search(app):
    """
    Creates in db some albums with special titles for search by title tests.
    """
    albums = [Album(title='search1'), Album(title='search2')]

    for a in albums:
        db.session.add(a)

    db.session.commit()

    yield albums

    for a in albums:
        db.session.delete(a)

    db.session.commit()
