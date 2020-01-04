import pytest
from werkzeug.security import generate_password_hash, check_password_hash
from ad_server import create_app, db
from ad_server.config import TestConfig
from flask_login import current_user
import ad_server.models as model
import json


@pytest.fixture(scope='module')
def test_client():
    app = create_app(TestConfig)

    context = app.app_context()
    context.push()

    db.create_all()

    user = model.User(login='TestUser', password='testpass')

    db.session.add(user)
    db.session.commit()

    yield app.test_client()

    db.drop_all()
    context.pop()


# TODO: Tests for logging if user is already logged in.
# Same for registration. Test logout for logged out user.

def test_password_hashing():
    """ Just in case """

    password = 'soverystrongpass'
    generted_hash = generate_password_hash(password)
    assert check_password_hash(generted_hash, password)


def test_get_created_user(test_client):
    """
    Test if sqlite database created in fixture is working
    and user named TestUser has been created
    """

    user = model.User.query.filter_by(login='TestUser').first()
    assert user


def test_user_registration(test_client):
    """
    Test new user registration.
    Server response and creation of new user record in database is tested.
    """

    data = {'login': 'TestUser2', 'pass': 'testpass'}
    response = test_client.post(
        '/api/public/auth/register',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
        )

    assert response.json.get('message') == 'Successful registration'
    assert response.status_code == 200
    assert model.User.query.filter_by(login='TestUser2').first()


def test_user_login(test_client):
    """
    Test for user logging in.
    Server response is checked and is_authenticated property of user.
    """
    user = model.User.query.filter_by(login='TestUser').first()

    assert not user.is_authenticated

    data = {'login': 'TestUser', 'pass': 'testpass'}
    response = test_client.post(
        '/api/public/auth/login',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )

    assert response.status_code == 200
    assert response.json.get('message') == 'Successful login'
    assert user.is_authenticated


def test_user_logout(test_client):
    pass
