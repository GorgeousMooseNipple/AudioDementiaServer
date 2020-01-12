from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from ad_server.models import User
from flask import g
import ad_server.views.errors as errors
import jwt


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user:
        g.current_user = user
        return user.check_password(password)
    else:
        return False


@basic_auth.error_handler
def basic_auth_error():
    return errors.unauthorized('You are not authorized')


@token_auth.verify_token
def verify_token(token):
    if token:
        try:
            g.current_user = User.validate_token(token)
            return g.current_user is not None
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError) as e:
            g.token_exception = e
            return False
    else:
        return False


@token_auth.error_handler
def token_auth_error():
    excp = g.token_exception
    if isinstance(excp, jwt.InvalidTokenError):
        pass
    elif isinstance(excp, jwt.ExpiredSignatureError):
        pass
    return errors.unauthorized('Token verification failed')
