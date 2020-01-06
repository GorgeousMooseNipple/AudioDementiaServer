from flask import Blueprint, request, jsonify
from ad_server.models import User
from ad_server import db
import ad_server.views.errors as errors


users = Blueprint('users', __name__)


def successful_response(message, data=None):
    response_data = {
        'message': message,
        'data': data
    }
    response = jsonify(response_data)
    response.status_code = 200
    return response


@users.route('/register', methods=['POST'])
def register_user():
    if current_user.is_authenticated:
        return errors.bad_request(
            'You are already authenticated. Please log out.')
    json_request = request.json
    login = json_request.get('login')
    password = json_request.get('pass')
    if not login or not password:
        return errors.bad_request(
            'Login and password required for registration')
    elif User.query.filter_by(login=login).first():
        return errors.bad_request('This username is already taken')
    else:
        user = User(login=login, password=password)
        db.session.add(user)
        db.session.commit()
        user.login_user()
    return successful_response('Successful registration')


@users.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return errors.bad_request(
            'You are already authenticated. Please log out.')
    json_request = request.json
    login = json_request.get('login')
    password = json_request.get('pass')
    if not login or not password:
        return errors.bad_request('Login or password is not provided')
    user = User.query.filter_by(login=login).first()
    if not user:
        return errors.bad_request('Incorrect login')
    elif not user.check_password(password):
        return errors.bad_request('Incorrect password')
    else:
        user.login_user()
        return successful_response('Successful login')


@users.route('/logout', methods=['GET'])
def logout():
    if current_user.is_authenticated:
        current_user.logout_user()
        return successful_response('User logged out')
    else:
        return errors.forbidden('You are not authorized')
