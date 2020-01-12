from flask import Blueprint, request, g
from ad_server.models import User, RefreshToken
from ad_server import db
from ad_server.views.auth import basic_auth, generate_token
import ad_server.views.messages as msg


users = Blueprint('users', __name__)


@users.route('/register', methods=['POST'])
def register_user():
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


@users.route('/token', methods=['POST'])
@basic_auth.login_required
def get_token():
    user = g.current_user
    access_token = generate_token(user.id)
    refreh_token = RefreshToken.create(user.id)
    db.session.commit()
    return msg.success(
        message='Access token retrieved',
        access_token=access_token,
        refresh_token=refreh_token)


@users.route('/token/refresh', methods=['POST'])
def refresh_token():
    json_request = request.json
    refresh_token = json_request.get('refresh_token')
    if not refresh_token:
        return msg.errors.bad_request(
            'You should provide refresh token for this call')
    refresh_token_obj = RefreshToken.valid_token(refresh_token)
    if not refresh_token_obj:
        return msg.errors.unauthorized('Provided token is not valid')
    access_token = generate_token(refresh_token_obj.user_id)
    return msg.success(
        message='Access token retrieved',
        access_token=access_token)


@users.route('/token/revoke', methods=['POST'])
def revoke_token():
    json_request = request.json
    refresh_token = json_request.get('refresh_token')
    if not refresh_token:
        return msg.errors.bad_request(
            'You should provide refresh token for this call')
    RefreshToken.revoke(refresh_token)
    db.session.commit()
    return msg.success('Token is successfully revoked')
