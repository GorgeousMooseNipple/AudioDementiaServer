import pytest
import requests
import os
import shutil
from ad_server import create_app, db
from ad_server.config import TestConfig
import ad_server.models as model
from flask import current_app


PWD = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope='module')
def test_app():
    app = create_app(TestConfig)
    context = app.app_context()
    context.push()

    db.create_all()

    user = model.User(login='TestUser', password='testpass')

    db.session.add(user)
    db.session.commit()

    yield {
        'app': app,
        'test_client': app.test_client(),
        'db': db
        }

    db.drop_all()
    context.pop()


@pytest.fixture(scope='module')
def audio_files_fixture():

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
