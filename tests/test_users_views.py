from werkzeug.security import generate_password_hash, check_password_hash
from ad_server.models import User
from ad_server.models import RefreshToken
from flask import url_for
import json
import base64
import time


def test_password_hashing():
    """ Just in case """

    password = 'soverystrongpass'
    generted_hash = generate_password_hash(password)
    assert check_password_hash(generted_hash, password)


def test_get_created_user():
    """
    Test if sqlite database created in fixture is working
    and user named TestUser has been created
    """

    user = User.query.filter_by(login='TestUser').first()
    assert user


def test_user_registration(test_client_json):
    """
    Test new user registration.
    Server response and creation of new user record in database is tested here.
    """

    data = {'login': 'TestUser2', 'pass': 'testpass'}
    response = test_client_json.post(
        url_for('users.register_user'),
        data=json.dumps(data)
        )

    assert response.json.get('message') == 'Successful registration'
    assert response.status_code == 200
    assert User.query.filter_by(login='TestUser2').first()


def test_get_token(test_client):
    """
    Testing process of retrieving access and refresh tokens by registered user.
    """

    login = 'TestUser'
    password = 'testpass'
    # Basic auth header Authorization: Basic login:password
    auth = base64.b64encode(
        bytes(login + ':' + password, 'utf-8')).decode('utf-8')

    headers = {'Authorization': f'Basic {auth}'}
    response = test_client.get(
        url_for('users.get_token'),
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


def test_refresh_token(test_client_json, user_with_tokens):
    """
    Test process of getting new access token by
    sending request with refresh token.
    """
    user, access, refresh = user_with_tokens

    # Wait 2 second just so new access token will be created using different
    # expiration time parameter and so won't be the same as the old one
    time.sleep(2)

    response = test_client_json.post(
        url_for('users.refresh_token'),
        data=json.dumps({'no_refresh_token': None})
    )

    assert response.status_code == 400
    assert response.json.get('message') == \
        'You should provide refresh token for this call'

    response = test_client_json.post(
        url_for('users.refresh_token'),
        data=json.dumps({'refresh_token': 'invalid'})
    )

    assert response.status_code == 401
    assert response.json.get('message') == \
        'Provided refresh token is not valid'

    response = test_client_json.post(
        url_for('users.refresh_token'),
        data=json.dumps({'refresh_token': refresh})
    )

    assert response.status_code == 200

    new_access_token = response.json.get('access_token')
    assert new_access_token
    assert new_access_token != access


def test_revoke_token(test_client_json, user_with_tokens):
    """
    Test revoking refresh token
    """
    user, access, refresh = user_with_tokens

    response = test_client_json.post(
        url_for('users.revoke_token'),
        data=json.dumps({'refresh_token': None})
    )

    assert response.status_code == 400

    response = test_client_json.post(
        url_for('users.revoke_token'),
        data=json.dumps({'refresh_token': refresh})
    )

    assert response.status_code == 200
    assert response.json.get('message') ==\
        'Token is successfully revoked'

    # Check if refresh token is revoked in db
    assert RefreshToken.valid_token(refresh) is None


def test_access_without_token(test_client):
    """
    Make call to test API endpoint which requires access token without token.
    """

    response = test_client.get(url_for('test_token_access'))

    assert response.status_code == 401
    assert response.json.get('message') ==\
        'Token verification failed'


def test_access_with_invalid_token(test_client):
    """
    Make call to test API endpoint which requires access  with invalid token
    """

    headers = {'Authorization': 'Bearer verynotvalidtoken'}

    response = test_client.get(
        url_for('test_token_access'),
        headers=headers
        )

    assert response.status_code == 401
    assert response.json.get('message') ==\
        'Invalid token'


def test_access_with_valid_token(test_client, user_with_tokens):
    """
    Make call to test API endpoint which requires access  with valid token.
    Just in case.
    """

    access_token = user_with_tokens[1]

    headers = {'Authorization': f'Bearer {access_token}'}

    response = test_client.get(
        url_for('test_token_access'),
        headers=headers
        )

    assert response.status_code == 200
    assert response.json.get('message') ==\
        'Successful API call with token required'
