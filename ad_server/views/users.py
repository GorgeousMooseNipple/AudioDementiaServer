from flask import Blueprint, request, g
from ad_server.models import User, RefreshToken
from ad_server import db
from ad_server.views.auth import basic_auth, generate_token
import ad_server.views.messages as msg


users = Blueprint('users', __name__)


@users.route('/user/new', methods=['POST'])
def register_user():
    """
    _server_/user/new POST
    Registers new app user.
    
    :param str login: new user's login POST request parameter 
    :param str pass: new user's password POST request parameter
    :return: response with fields _status_ and _message_
    """
    json_request = request.json
    login = json_request.get('login')
    password = json_request.get('pass')
    if not login or not password:
        return msg.errors.bad_request(
            'Login and password required for registration')
    elif User.query.filter_by(login=login).first():
        return msg.errors.bad_request('This username is already taken')
    else:
        user = User(login=login, password=password)
        db.session.add(user)
        db.session.commit()
    return msg.success('Successful registration')


@users.route('/token/new', methods=['GET'])
@basic_auth.login_required
def get_token():
    """
    _server_/token/new GET
    Generates access token for user. Must be provided with Authorization header in format:
    Authorization: Basic login:pass

    :return: response with fields _status_, _message_, _access_token and _refresh_token_
    """
    user = g.current_user
    access_token = generate_token(user.id)
    refreh_token = RefreshToken.create_or_get(user.id)
    db.session.commit()
    return msg.success(
        message='Access token retrieved',
        id=user.id,
        access_token=access_token,
        refresh_token=refreh_token)


@users.route('/token/refresh', methods=['POST'])
def refresh_token():
    """
    _server_/auth/token/refresh POST
    Uses refresh token to generate new valid token for user.

    :param str refresh_token: refresh token must be present in request field refresh_token
    :return: response with fields _status_, _message_ and _access_token_
    """
    json_request = request.json
    refresh_token = json_request.get('refresh_token')
    if not refresh_token:
        return msg.errors.bad_request(
            'You should provide refresh token for this call')
    refresh_token_obj = RefreshToken.valid_token(refresh_token)
    if not refresh_token_obj:
        return msg.errors.unauthorized('Provided refresh token is not valid')
    access_token = generate_token(refresh_token_obj.user_id)
    return msg.success(
        message='New access token generated',
        access_token=access_token)


@users.route('/token/revoke', methods=['POST'])
def revoke_token():
    """
    _server_/auth/token/revoke POST
    Revokes refresh token.

    :param str refresh_token: refresh token must be present in request field refresh_token
    :return: response with fields _status_ and _message_
    """
    json_request = request.json
    refresh_token = json_request.get('refresh_token')
    if not refresh_token:
        return msg.errors.bad_request(
            'You should provide refresh token for this call')
    RefreshToken.revoke(refresh_token)
    db.session.commit()
    return msg.success('Token is successfully revoked')
