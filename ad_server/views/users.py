from flask import Blueprint, request, jsonify
from flask_login import current_user, login_user, logout_user
from ad_server.models import User
from ad_server import login, db
import ad_server.views.errors as errors


users = Blueprint('users', __name__)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


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
        pass
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
        login_user(user, remember=False)
    return successful_response('Successful registration')


@users.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        pass
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
        return successful_response('Successful login')


@users.route('/logout', methods=['GET'])
def logout():
    logout_user()
    return successful_response('User logged out')
