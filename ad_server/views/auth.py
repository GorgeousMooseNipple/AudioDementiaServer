from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth
from ad_server.models import User
import ad_server.views.errors as errors


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()


@basic_auth.verify_password
def verify_user(login, password):
    user = User.query.filter_by(login=login).first()
    if user:
        return user.check_password(password)
    else:
        return False


@basic_auth.error_handler
def basic_auth_error():
    return errors.unauthorized('You are no authorized')


@token_auth.verify_token
def verify_token(token):
    pass


@token_auth.error_handler
def token_auth_error():
    return errors.unauthorized('Token verification failed')
