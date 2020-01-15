import pytest
import requests
import os
import shutil
import ad_server.views.messages as msg
from ad_server import create_app, db
from ad_server.config import TestConfig
from ad_server.models import User, RefreshToken
from ad_server.views.auth import generate_token, token_auth
from flask import current_app, testing


PWD = os.path.dirname(os.path.abspath(__file__))


class TestClient(testing.FlaskClient):
    """
    Custom flask test client with default headers
    """
    def open(self, *args, **kwargs):
        default_headers = {
            'Content-Type': 'application/json'
        }
        headers = kwargs.pop('headers', {})
        headers.update(default_headers)
        kwargs['headers'] = headers
        return super().open(*args, **kwargs)


@pytest.fixture(scope='module')
def test_app():
    """
    This module level fixture creates test application and sqlite database
    Gives test functions access to application, database and test client
    """
    app = create_app(TestConfig)
    context = app.test_request_context()
    context.push()

    # Add fake endpoint wich require token for access
    @app.route('/test/token/access', methods=['GET'])
    @token_auth.login_required
    def test_token_access():
        return msg.success('Successful API call with token required')

    db.create_all()

    user = User(login='TestUser', password='testpass')
    logged_user = User(login='LoggedUser', password='testpass')

    db.session.add(user)
    db.session.add(logged_user)
    db.session.commit()

    app.test_client_class = TestClient
    test_client = app.test_client()
    headers = {'Content-Type': 'application/json'}
    test_client.options(headers=headers)

    yield {
        'app': app,
        'test_client': app.test_client(),
        'db': db
        }

    db.drop_all()
    os.remove(os.path.join(PWD, 'test.db'))
    context.pop()


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

    data = (user, access_token, refresh_token)

    yield data

    RefreshToken.revoke(refresh_token)
    db.session.commit()


@pytest.fixture(scope='module')
def audio_files_fixture():
    """
    This fixture downloads and prepares mp3 files for tests
    to test adding such files into database
    """

    media_folder = os.path.join(PWD, 'test_media')
    old_storage = current_app.config['MEDIA_STORAGE']
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
    current_app.config['MEDIA_STORAGE'] = old_storage
