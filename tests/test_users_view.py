from werkzeug.security import generate_password_hash, check_password_hash
from ad_server.models import User
import json
import tests.conftest


# TODO: Tests for logging if user is already logged in.
# Same for registration. Test logout for logged out user.
test_app = tests.conftest.test_app


def test_password_hashing():
    """ Just in case """

    password = 'soverystrongpass'
    generted_hash = generate_password_hash(password)
    assert check_password_hash(generted_hash, password)


def test_get_created_user(test_app):
    """
    Test if sqlite database created in fixture is working
    and user named TestUser has been created
    """

    user = User.query.filter_by(login='TestUser').first()
    assert user


def test_user_registration(test_app):
    """
    Test new user registration.
    Server response and creation of new user record in database is tested.
    """
    test_client = test_app['test_client']

    data = {'login': 'TestUser2', 'pass': 'testpass'}
    response = test_client.post(
        '/api/public/auth/register',
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
        )

    assert response.json.get('message') == 'Successful registration'
    assert response.status_code == 200
    assert User.query.filter_by(login='TestUser2').first()


def test_user_login(test_app):
    """
    Test for user logging in.
    Server response is checked and is_authenticated property of user.
    """
    test_client = test_app['test_client']

    user = User.query.filter_by(login='TestUser').first()

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


def test_user_logout(test_app):
    pass
