from werkzeug.http import HTTP_STATUS_CODES
from flask import jsonify


def error(status, message=''):
    response_data = {
        'error': HTTP_STATUS_CODES.get(status, 'Internal Server Error'),
        'message': message
    }
    response = jsonify(response_data)
    response.status_code = status
    return response


def bad_request(message=''):
    return error(400, message=message)


def internal_error(message=''):
    return error(500, message=message)


def forbidden(message=''):
    return error(403, message=message)


def not_found(message=''):
    return error(404, message=message)
