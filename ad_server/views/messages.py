from werkzeug.http import HTTP_STATUS_CODES
from flask import jsonify


class Message:
    @staticmethod
    def send_message(status_code, message, **kwargs):
        response_data = {
            'status': HTTP_STATUS_CODES.get(
                status_code, 'Internal Server Error'),
            'message': message
        }

        for k, v in kwargs.items():
            response_data[k] = v

        response = jsonify(response_data)
        response.status_code = status_code
        return response


class ErrorMessage(Message):
    def bad_request(self, message=''):
        return self.send_message(400, message=message)

    def internal_error(self, message=''):
        return self.send_message(500, message=message)

    def forbidden(self, message=''):
        return self.send_message(403, message=message)

    def not_found(self, message=''):
        return self.send_message(404, message=message)

    def unauthorized(self, message=''):
        return self.send_message(401, message=message)


errors = ErrorMessage()


def success(message='', status_code=200, **kwargs):
    return Message.send_message(status_code, message, **kwargs)
