from werkzeug.security import generate_password_hash, check_password_hash
from ad_server.models import User
from ad_server.models import RefreshToken
import json
import tests.conftest as fix
import base64
import time


test_app = fix.test_app
user_with_tokens = fix.user_with_tokens


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
    Server response and creation of new user record in database is tested here.
    """
    test_client = test_app['test_client']

    data = {'login': 'TestUser2', 'pass': 'testpass'}
    response = test_client.post(
        '/api/public/auth/register',
        data=json.dumps(data)
        )

    assert response.json.get('message') == 'Successful registration'
    assert response.status_code == 200
    assert User.query.filter_by(login='TestUser2').first()


def test_get_token(test_app):
    """
    Testing process of retrieving access and refresh tokens by registered user.
    """
    test_client = test_app['test_client']

    login = 'TestUser'
    password = 'testpass'
    # Basic auth header Authorization: Basic login:password
    auth = base64.b64encode(
        bytes(login + ':' + password, 'utf-8')).decode('utf-8')

    headers = {'Authorization': f'Basic {auth}'}
    response = test_client.get(
        '/api/public/auth/token',
        headers=headers
    )

    # Check if status is ok and response received in json
    assert response.status_code == 200
    assert response.is_json

    # Response contains access_token
    access_token = response.json.get('access_token')
    assert access_token

    # Response contains refresh_token
    refresh_token = response.json.get('refresh_token')
    assert refresh_token

    message = response.json.get('message')
    assert message == 'Access token retrieved'


def test_refresh_token(test_app, user_with_tokens):
    """
    Test process of getting new access token by
    sending request with refresh token.
    """
    test_client = test_app['test_client']
    user, access, refresh = user_with_tokens

    # Wait 2 second just so new access token will be created using different
    # expiration time parameter and so won't be the same as the old one
    time.sleep(2)

    response = test_client.post(
        'api/public/auth/token/refresh',
        data=json.dumps({'no_refresh_token': None})
    )

    assert response.status_code == 400
    assert response.json.get('message') == \
        'You should provide refresh token for this call'

    response = test_client.post(
        'api/public/auth/token/refresh',
        data=json.dumps({'refresh_token': 'invalid'})
    )

    assert response.status_code == 401
    assert response.json.get('message') == \
        'Provided token is not valid'

    response = test_client.post(
        'api/public/auth/token/refresh',
        data=json.dumps({'refresh_token': refresh})
    )

    assert response.status_code == 200

    new_access_token = response.json.get('access_token')
    assert new_access_token
    assert new_access_token != access


def test_revoke_token(test_app, user_with_tokens):
    """
    Test revoking refresh token
    """
    test_client = test_app['test_client']
    user, access, refresh = user_with_tokens

    response = test_client.post(
        '/api/public/auth/token/revoke',
        data=json.dumps({'refresh_token': None})
    )

    assert response.status_code == 400

    response = test_client.post(
        '/api/public/auth/token/revoke',
        data=json.dumps({'refresh_token': refresh})
    )

    assert response.status_code == 200
    assert response.json.get('message') ==\
        'Token is successfully revoked'

    # Check if refresh token is revoked in db
    assert RefreshToken.valid_token(refresh) is None


def test_access_without_token(test_app):
    """
    Make call to test API endpoint which requires access token without token.
    """
    test_client = test_app['test_client']

    response = test_client.get('/test/token/access')

    assert response.status_code == 401
    assert response.json.get('message') ==\
        'Token verification failed'


def test_access_with_invalid_token(test_app):
    """
    Make call to test API endpoint which requires access  with invalid token
    """
    test_client = test_app['test_client']

    headers = {'Authorization': 'Bearer verynotvalidtoken'}

    response = test_client.get(
        '/test/token/access',
        headers=headers
        )

    assert response.status_code == 401
    assert response.json.get('message') ==\
        'Invalid token'


def test_access_with_valid_token(test_app, user_with_tokens):
    """
    Make call to test API endpoint which requires access  with valid token.
    Just in case.
    """
    test_client = test_app['test_client']

    access_token = user_with_tokens[1]

    headers = {'Authorization': f'Bearer {access_token}'}

    response = test_client.get(
        '/test/token/access',
        headers=headers
        )

    assert response.status_code == 200
    assert response.json.get('message') ==\
        'Successful API call with token required'
