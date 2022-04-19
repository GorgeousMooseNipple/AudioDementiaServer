from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from ad_server.models import User
from flask import g, current_app
from datetime import datetime, timedelta
import ad_server.views.messages as msg
import jwt


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


def generate_token(user_id, expires_in=timedelta(hours=24)):
    if isinstance(expires_in, int):
        delta = timedelta(seconds=expires_in)
    elif isinstance(expires_in, timedelta):
        delta = expires_in
    else:
        raise TypeError(
            'expires_in value must be either integer in seconds or'
            'datetime.timedelta'
        )
    payload = {
        'id': user_id,
        'exp': datetime.utcnow() + delta
        }
    secret = current_app.config.get('SECRET_KEY')
    return jwt.encode(payload, secret, algorithm='HS256')


def validate_token(token):
    secret = current_app.config.get('SECRET_KEY')
    payload = jwt.decode(token, secret, algorithms='HS256')
    id = payload.get('id')
    return User.query.get(int(id))


@basic_auth.verify_password
def verify_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user:
        # Store this user in request context
        g.current_user = user
        return user.check_password(password)
    else:
        return False


@basic_auth.error_handler
def basic_auth_error():
    return msg.errors.unauthorized('Invalid credentials')


@token_auth.verify_token
def verify_token(token):
    if token:
        try:
            g.current_user = validate_token(token)
            return g.current_user is not None
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            g.token_exception = e
            return False
    else:
        return False


@token_auth.error_handler
def token_auth_error():
    try:
        excp = g.token_exception
        if isinstance(excp, jwt.ExpiredSignatureError):
            return msg.errors.unauthorized('Token has expired')
        elif isinstance(excp, jwt.InvalidTokenError):
            return msg.errors.unauthorized('Invalid token')
    except AttributeError:
        return msg.errors.unauthorized('Token verification failed')
